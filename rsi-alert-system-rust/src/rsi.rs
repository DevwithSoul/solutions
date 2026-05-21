/// Result of an RSI calculation for a single trading pair.
#[derive(Debug, Clone)]
pub struct RsiResult {
    /// Current RSI value (0.0–100.0)
    pub rsi: f64,
}

/// Errors during RSI calculation.
#[derive(Debug)]
pub enum RsiError {
    InsufficientData { needed: usize, got: usize },
}

impl std::fmt::Display for RsiError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RsiError::InsufficientData { needed, got } => {
                write!(f, "Need at least {needed} data points, got {got}")
            }
        }
    }
}

/// Calculate RSI using Wilder's Smoothing Method.
///
/// Standard period is 14. Requires at least `period + 1` closing prices.
///
/// Formula:
/// - RSI = 100 - (100 / (1 + RS))
/// - RS = Average Gain / Average Loss
/// - Average Gain = (prev_avg_gain * (period-1) + current_gain) / period
/// - Average Loss = (prev_avg_loss * (period-1) + current_loss) / period
pub fn calculate_rsi(closes: &[f64], period: usize) -> Result<RsiResult, RsiError> {
    if closes.len() < period + 1 {
        return Err(RsiError::InsufficientData {
            needed: period + 1,
            got: closes.len(),
        });
    }

    // Calculate price changes
    let mut gains = Vec::with_capacity(closes.len() - 1);
    let mut losses = Vec::with_capacity(closes.len() - 1);

    for i in 1..closes.len() {
        let change = closes[i] - closes[i - 1];
        gains.push(change.max(0.0));
        losses.push((-change).max(0.0));
    }

    // Initial SMA for the first `period` gains/losses
    let first_gains: f64 = gains[..period].iter().sum();
    let first_losses: f64 = losses[..period].iter().sum();
    let mut avg_gain = first_gains / period as f64;
    let mut avg_loss = first_losses / period as f64;

    if avg_loss == 0.0 {
        // If no losses at all, RSI is 100 (the asset only went up)
        return Ok(RsiResult { rsi: 100.0 });
    }

    // Wilder's smoothing for remaining values
    let mut rsi_values = Vec::new();

    // RSI for the first period (initial SMA-based)
    let rs = avg_gain / avg_loss;
    let rsi_first = 100.0 - (100.0 / (1.0 + rs));
    rsi_values.push(rsi_first);

    // Remaining RSI values using Wilder's smoothing
    for i in period..gains.len() {
        avg_gain = ((avg_gain * (period as f64 - 1.0)) + gains[i]) / period as f64;
        avg_loss = ((avg_loss * (period as f64 - 1.0)) + losses[i]) / period as f64;

        if avg_loss == 0.0 {
            rsi_values.push(100.0);
        } else {
            let rs = avg_gain / avg_loss;
            let rsi = 100.0 - (100.0 / (1.0 + rs));
            rsi_values.push(rsi);
        }
    }

    // The last RSI value is our current RSI
    let current_rsi = *rsi_values.last().unwrap_or(&50.0);

    Ok(RsiResult { rsi: current_rsi })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rsi_constant_up() {
        // All prices going up → RSI should be 100
        let closes: Vec<f64> = (0..30).map(|i| 100.0 + i as f64).collect();
        let result = calculate_rsi(&closes, 14).unwrap();
        assert!((result.rsi - 100.0).abs() < 0.01);
    }

    #[test]
    fn test_rsi_constant_down() {
        // All prices going down → RSI should be 0
        let closes: Vec<f64> = (0..30).map(|i| 100.0 - i as f64).collect();
        let result = calculate_rsi(&closes, 14).unwrap();
        assert!((result.rsi - 0.0).abs() < 0.01);
    }

    #[test]
    fn test_rsi_not_enough_data() {
        let closes = vec![100.0];
        let result = calculate_rsi(&closes, 14);
        assert!(result.is_err());
    }

    #[test]
    fn test_rsi_mid_range() {
        // Alternating up/down → RSI should be around 50
        let closes: Vec<f64> = (0..100).map(|i| 100.0 + (i % 2) as f64 * 2.0).collect();
        let result = calculate_rsi(&closes, 14).unwrap();
        assert!((result.rsi - 50.0).abs() < 10.0);
    }
}
