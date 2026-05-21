use chrono::Utc;
use serde::Deserialize;

/// A single kline (candlestick) from the Binance API.
///
/// Binance returns a JSON array with positional values:
///   [open_time, open, high, low, close, volume, close_time, quote_vol, trades,
///    taker_base_vol, taker_quote_vol, ignore]
#[derive(Debug, Deserialize)]
struct Kline(
    #[allow(dead_code)] i64,    // 0: open time
    #[allow(dead_code)] String, // 1: open
    #[allow(dead_code)] String, // 2: high
    #[allow(dead_code)] String, // 3: low
    String,                     // 4: close
    #[allow(dead_code)] String, // 5: volume
    #[allow(dead_code)] i64,    // 6: close time
    #[allow(dead_code)] String, // 7: quote asset volume
    #[allow(dead_code)] i64,    // 8: number of trades
    #[allow(dead_code)] String, // 9: taker buy base asset volume
    #[allow(dead_code)] String, // 10: taker buy quote asset volume
    #[allow(dead_code)] String, // 11: ignore
);

/// Raw price data fetched from Binance.
#[derive(Debug, Clone)]
pub struct PriceData {
    pub closes: Vec<f64>,
    pub current_price: f64,
    pub timestamp: i64,
}

/// Errors from Binance API interaction.
#[derive(Debug)]
pub enum BinanceError {
    Http(String),
    Parse(String),
}

impl std::fmt::Display for BinanceError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BinanceError::Http(msg) => write!(f, "HTTP error: {msg}"),
            BinanceError::Parse(msg) => write!(f, "Parse error: {msg}"),
        }
    }
}

/// Fetch kline data from Binance for a given symbol and interval.
///
/// Returns closing prices and the latest price. Fetches `rsi_period + 50` candles
/// to have enough data for a stable RSI calculation.
pub async fn fetch_klines(
    symbol: &str,
    interval: &str,
    rsi_period: usize,
) -> Result<PriceData, BinanceError> {
    let limit = (rsi_period + 50).max(100);
    let url = format!(
        "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}",
        symbol, interval, limit
    );

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| BinanceError::Http(e.to_string()))?;

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| BinanceError::Http(e.to_string()))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(BinanceError::Http(format!(
            "API returned {status}: {body}"
        )));
    }

    let klines: Vec<Kline> = response
        .json()
        .await
        .map_err(|e| BinanceError::Parse(e.to_string()))?;

    if klines.is_empty() {
        return Err(BinanceError::Parse("Empty kline response".into()));
    }

    let closes: Vec<f64> = klines
        .iter()
        .map(|k| k.4.parse::<f64>().unwrap_or(0.0))
        .collect();

    let current_price = *closes.last().unwrap_or(&0.0);
    let timestamp = Utc::now().timestamp();

    Ok(PriceData {
        closes,
        current_price,
        timestamp,
    })
}
