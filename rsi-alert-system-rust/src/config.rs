use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Persistent application configuration stored as JSON on disk.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Binance trading pairs to monitor, e.g. ["BTCUSDT", "ETHUSDT"]
    pub coins: Vec<String>,
    /// Kline interval: "1m", "5m", "15m", "30m", "1h", "4h", "1d"
    pub interval: String,
    /// RSI period (standard: 14)
    pub rsi_period: usize,
    /// RSI above this triggers overbought alert
    pub overbought_threshold: f64,
    /// RSI below this triggers oversold alert
    pub oversold_threshold: f64,
    /// Seconds between data fetches from Binance
    pub check_interval_secs: u64,
    /// Enable browser notification sound
    pub sound_enabled: bool,
    /// Enable browser desktop notifications
    pub notifications_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            coins: vec!["BTCUSDT".to_string()],
            interval: "1h".to_string(),
            rsi_period: 14,
            overbought_threshold: 70.0,
            oversold_threshold: 30.0,
            check_interval_secs: 60,
            sound_enabled: false,
            notifications_enabled: false,
        }
    }
}

impl Config {
    /// Path to the settings JSON file (next to the binary).
    fn path() -> PathBuf {
        let exe = std::env::current_exe().unwrap_or_default();
        let dir = exe.parent().unwrap_or(std::path::Path::new("."));
        dir.join("rsi_settings.json")
    }

    /// Load config from disk, or return default if file doesn't exist.
    pub fn load() -> Self {
        let path = Self::path();
        if path.exists() {
            match fs::read_to_string(&path) {
                Ok(content) => {
                    match serde_json::from_str(&content) {
                        Ok(cfg) => {
                            tracing::info!("Config loaded from {:?}", path);
                            return cfg;
                        }
                        Err(e) => {
                            tracing::warn!("Failed to parse config, using defaults: {e}");
                        }
                    }
                }
                Err(e) => {
                    tracing::warn!("Failed to read config file: {e}");
                }
            }
        }
        let cfg = Config::default();
        cfg.save();
        cfg
    }

    /// Save config to disk.
    pub fn save(&self) {
        let path = Self::path();
        let content = serde_json::to_string_pretty(self).unwrap();
        if let Err(e) = fs::write(&path, &content) {
            tracing::error!("Failed to write config: {e}");
        } else {
            tracing::info!("Config saved to {:?}", path);
        }
    }
}

/// Shared config handle for the application.
pub type SharedConfig = Arc<RwLock<Config>>;

pub fn new_shared_config() -> SharedConfig {
    Arc::new(RwLock::new(Config::load()))
}
