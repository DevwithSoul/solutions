mod binance;
mod config;
mod rsi;

use axum::{
    extract::State,
    response::{
        sse::{Event, KeepAlive},
        Html, Sse,
    },
    routing::get,
    Json, Router,
};
use chrono::Utc;
use config::{new_shared_config, Config, SharedConfig};
use futures::future::ready;
use futures::stream::{Stream, StreamExt};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::convert::Infallible;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::broadcast;
use tokio_stream::wrappers::BroadcastStream;
use tracing_subscriber::EnvFilter;

/// Message pushed to the browser via SSE.
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", content = "data")]
enum SseMessage {
    /// Regular RSI update for a coin
    #[serde(rename = "update")]
    Update(CoinRsiData),
    /// Alert condition triggered
    #[serde(rename = "alert")]
    Alert(AlertData),
    /// Full snapshot of all tracked coins
    #[serde(rename = "snapshot")]
    Snapshot(Vec<CoinRsiData>),
}

/// RSI data for a single coin, sent to clients.
#[derive(Debug, Clone, Serialize)]
pub struct CoinRsiData {
    pub symbol: String,
    pub display_name: String,
    pub rsi: f64,
    pub price: f64,
    pub timestamp: i64,
    pub alert: Option<String>,
}

/// Alert data sent when threshold is crossed.
#[derive(Debug, Clone, Serialize)]
pub struct AlertData {
    pub symbol: String,
    pub display_name: String,
    pub rsi: f64,
    pub price: f64,
    pub alert_type: String, // "overbought" or "oversold"
    pub message: String,
    pub timestamp: i64,
}

// ── Shared Application State ──────────────────────────────────────────────

struct AppState {
    config: SharedConfig,
    /// Latest RSI data for each tracked coin, keyed by symbol
    rsi_data: tokio::sync::RwLock<HashMap<String, CoinRsiData>>,
    /// Broadcast channel to push updates to all connected SSE clients
    tx: broadcast::Sender<SseMessage>,
}

fn display_name(symbol: &str) -> String {
    symbol.trim_end_matches("USDT").to_string()
}

// ── HTTP Handlers ─────────────────────────────────────────────────────────

/// Serve the embedded dashboard HTML.
async fn index_handler() -> Html<&'static str> {
    Html(include_str!("../static/index.html"))
}

/// GET /api/rsi — returns current RSI data for all tracked coins.
async fn get_rsi_handler(
    State(state): State<Arc<AppState>>,
) -> Json<Vec<CoinRsiData>> {
    let data = state.rsi_data.read().await;
    let values: Vec<CoinRsiData> = data.values().cloned().collect();
    Json(values)
}

/// GET /api/config — returns current configuration.
async fn get_config_handler(
    State(state): State<Arc<AppState>>,
) -> Json<Config> {
    let cfg = state.config.read().await;
    Json(cfg.clone())
}

/// POST /api/config — update configuration.
#[derive(Deserialize)]
struct ConfigUpdate {
    coins: Option<Vec<String>>,
    interval: Option<String>,
    rsi_period: Option<usize>,
    overbought_threshold: Option<f64>,
    oversold_threshold: Option<f64>,
    check_interval_secs: Option<u64>,
    sound_enabled: Option<bool>,
    notifications_enabled: Option<bool>,
}

async fn post_config_handler(
    State(state): State<Arc<AppState>>,
    Json(update): Json<ConfigUpdate>,
) -> Json<Config> {
    let mut cfg = state.config.write().await;

    if let Some(coins) = update.coins {
        if !coins.is_empty() {
            cfg.coins = coins;
        }
    }
    if let Some(interval) = update.interval {
        cfg.interval = interval;
    }
    if let Some(period) = update.rsi_period {
        if period >= 2 {
            cfg.rsi_period = period;
        }
    }
    if let Some(val) = update.overbought_threshold {
        cfg.overbought_threshold = val.clamp(50.0, 100.0);
    }
    if let Some(val) = update.oversold_threshold {
        cfg.oversold_threshold = val.clamp(0.0, 50.0);
    }
    if let Some(val) = update.check_interval_secs {
        cfg.check_interval_secs = val.max(10);
    }
    if let Some(val) = update.sound_enabled {
        cfg.sound_enabled = val;
    }
    if let Some(val) = update.notifications_enabled {
        cfg.notifications_enabled = val;
    }

    cfg.save();
    tracing::info!("Configuration updated");

    let cloned = cfg.clone();
    Json(cloned)
}

/// GET /events — SSE endpoint for real-time RSI updates.
async fn sse_handler(
    State(state): State<Arc<AppState>>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let rx = state.tx.subscribe();

    // Send a snapshot immediately on connect
    let data = state.rsi_data.read().await;
    let snapshot: Vec<CoinRsiData> = data.values().cloned().collect();
    if !snapshot.is_empty() {
        let msg = SseMessage::Snapshot(snapshot);
        let _ = state.tx.send(msg);
    }
    drop(data);

    let stream = BroadcastStream::new(rx).filter_map(|result| {
        ready(match result {
            Ok(msg) => {
                let json = serde_json::to_string(&msg).unwrap_or_default();
                Some(Ok(Event::default().data(json)))
            }
            Err(_) => None, // lagged -> skip
        })
    });

    Sse::new(stream).keep_alive(
        KeepAlive::new()
            .interval(Duration::from_secs(15))
            .text("ping"),
    )
}

// ── Background Monitor ────────────────────────────────────────────────────

/// Background task that periodically fetches Binance data, calculates RSI,
/// detects alerts, and broadcasts results via SSE.
async fn monitor_loop(state: Arc<AppState>) {
    // Warm-up delay to let the server start
    tokio::time::sleep(Duration::from_secs(2)).await;

    loop {
        let (coins, interval, rsi_period, overbought, oversold) = {
            let cfg = state.config.read().await;
            (
                cfg.coins.clone(),
                cfg.interval.clone(),
                cfg.rsi_period,
                cfg.overbought_threshold,
                cfg.oversold_threshold,
            )
        };

        for symbol in &coins {
            match binance::fetch_klines(symbol, &interval, rsi_period).await {
                Ok(price_data) => {
                    match rsi::calculate_rsi(&price_data.closes, rsi_period) {
                        Ok(result) => {
                            let coin_data = CoinRsiData {
                                symbol: symbol.clone(),
                                display_name: display_name(symbol),
                                rsi: result.rsi,
                                price: price_data.current_price,
                                timestamp: price_data.timestamp,
                                alert: None,
                            };

                            // Check for alert conditions
                            let alert = check_alert(
                                symbol,
                                result.rsi,
                                price_data.current_price,
                                overbought,
                                oversold,
                            );

                            // Store the latest data
                            {
                                let mut data = state.rsi_data.write().await;
                                data.insert(symbol.clone(), coin_data.clone());
                            }

                            // Broadcast update
                            let msg = SseMessage::Update(coin_data);
                            let _ = state.tx.send(msg);

                            // Broadcast alert if triggered
                            if let Some(alert_data) = alert {
                                tracing::warn!(
                                    "ALERT: {} RSI={:.1} — {}",
                                    alert_data.symbol,
                                    alert_data.rsi,
                                    alert_data.alert_type
                                );
                                let alert_msg = SseMessage::Alert(alert_data);
                                let _ = state.tx.send(alert_msg);
                            }
                        }
                        Err(e) => {
                            tracing::error!("RSI calc failed for {symbol}: {e}");
                        }
                    }
                }
                Err(e) => {
                    tracing::error!("Binance fetch failed for {symbol}: {e}");
                }
            }

            // Small delay between fetching different coins to avoid rate limiting
            tokio::time::sleep(Duration::from_millis(500)).await;
        }

        // Wait for the configured interval before next full cycle
        let check_interval = {
            let cfg = state.config.read().await;
            cfg.check_interval_secs
        };
        tokio::time::sleep(Duration::from_secs(check_interval)).await;
    }
}

/// Check if RSI crossed a threshold and return alert data if so.
fn check_alert(
    symbol: &str,
    rsi: f64,
    price: f64,
    overbought: f64,
    oversold: f64,
) -> Option<AlertData> {
    let now = Utc::now().timestamp();
    let display = display_name(symbol);

    if rsi >= overbought {
        Some(AlertData {
            symbol: symbol.to_string(),
            display_name: display.clone(),
            rsi,
            price,
            alert_type: "overbought".to_string(),
            message: format!(
                "{} RSI is {:.1} — overbought (>{})!",
                display, rsi, overbought
            ),
            timestamp: now,
        })
    } else if rsi <= oversold {
        Some(AlertData {
            symbol: symbol.to_string(),
            display_name: display.clone(),
            rsi,
            price,
            alert_type: "oversold".to_string(),
            message: format!(
                "{} RSI is {:.1} — oversold (<{})!",
                display, rsi, oversold
            ),
            timestamp: now,
        })
    } else {
        None
    }
}

// ── Main ──────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .init();

    tracing::info!("Starting RSI Alert System...");

    let config = new_shared_config();
    {
        let cfg = config.read().await;
        tracing::info!(
            "Monitoring {} coins at {} interval",
            cfg.coins.len(),
            cfg.interval
        );
        tracing::info!(
            "Overbought threshold: {}, Oversold threshold: {}",
            cfg.overbought_threshold,
            cfg.oversold_threshold
        );
    }

    let (tx, _rx) = broadcast::channel::<SseMessage>(256);

    let state = Arc::new(AppState {
        config,
        rsi_data: tokio::sync::RwLock::new(HashMap::new()),
        tx,
    });

    // Start background monitor
    let monitor_state = state.clone();
    tokio::spawn(async move {
        monitor_loop(monitor_state).await;
    });

    // Build router
    let app = Router::new()
        .route("/", get(index_handler))
        .route("/api/rsi", get(get_rsi_handler))
        .route("/api/config", get(get_config_handler).post(post_config_handler))
        .route("/events", get(sse_handler))
        .with_state(state);

    // Try to bind on a free port, starting from 3000
    let listener = find_free_port("127.0.0.1", 3000, 3100).await;
    let addr = listener.local_addr().unwrap();
    tracing::info!("Dashboard: http://{addr}");
    tracing::info!("Press Ctrl+C to stop");

    axum::serve(listener, app).await.unwrap();
}

/// Try binding to a port in [start, end). Returns the first successful listener.
async fn find_free_port(host: &str, start: u16, end: u16) -> tokio::net::TcpListener {
    for port in start..end {
        let addr = format!("{host}:{port}");
        match tokio::net::TcpListener::bind(&addr).await {
            Ok(listener) => {
                tracing::info!("Bound to port {port}");
                return listener;
            }
            Err(e) => {
                tracing::warn!("Port {port} unavailable ({e}), trying next...");
                continue;
            }
        }
    }
    panic!("No free port found in range {start}–{end}");
}
