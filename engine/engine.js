'use strict';

function ema(values, period) {
  if (!Number.isInteger(period) || period <= 0) {
    throw new Error('period must be a positive integer');
  }
  if (values.length === 0) return [];

  const alpha = 2 / (period + 1);
  const result = [values[0]];
  for (let i = 1; i < values.length; i += 1) {
    result.push(alpha * values[i] + (1 - alpha) * result[i - 1]);
  }
  return result;
}

function emaCrossSignals(prices, fastPeriod = 3, slowPeriod = 5) {
  if (fastPeriod >= slowPeriod) {
    throw new Error('fastPeriod must be less than slowPeriod');
  }
  const fast = ema(prices, fastPeriod);
  const slow = ema(prices, slowPeriod);
  const signals = [];

  for (let i = 1; i < prices.length; i += 1) {
    if (fast[i - 1] <= slow[i - 1] && fast[i] > slow[i]) {
      signals.push({ index: i, price: prices[i], signal: 'BUY' });
    } else if (fast[i - 1] >= slow[i - 1] && fast[i] < slow[i]) {
      signals.push({ index: i, price: prices[i], signal: 'SELL' });
    }
  }
  return signals;
}

module.exports = { ema, emaCrossSignals };

if (require.main === module) {
  // Deterministic fake prices for a local smoke test; no external data or orders.
  const fakePrices = [10, 9, 8, 7, 6, 5, 6, 7, 8, 9, 10, 9, 8, 7, 6];
  const signals = emaCrossSignals(fakePrices, 3, 5);
  console.log('Fake-data EMA-cross signals:');
  console.log(signals);
}
