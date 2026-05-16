/** Shared API types matching backend Pydantic / SQLAlchemy. */

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  market: 'US_STOCK' | 'CRYPTO';
  asset_type: 'STOCK' | 'ETF' | 'CRYPTO';
  sector: string | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface Candle {
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  adjustment: string;
  is_final: boolean;
}

export interface PortfolioSnapshot {
  cash: string;
  equity: string;
  market_value: string;
  us_stock_exposure: string;
  crypto_exposure: string;
  daily_pnl: string;
  total_return_pct: string;
  max_drawdown_pct: string;
  open_positions_count: number;
  consecutive_losses: number;
  timestamp?: string;
}

export interface RegimeRow {
  timestamp?: string;
  regime: string | null;
  spy_above_ma200?: boolean;
  spy_above_ma50?: boolean;
  vix_level?: string | null;
  btc_above_ma200?: boolean;
  notes?: string;
}

export interface SignalRow {
  id: number;
  symbol: string;
  market: string;
  direction: string;
  signal_type: string;
  current_price: string;
  entry_low: string | null;
  entry_high: string | null;
  stop_loss: string | null;
  target_1: string | null;
  target_2: string | null;
  confidence_score: number;
  risk_reward_ratio: string | null;
  position_size_pct: string | null;
  expected_holding_days_min: number | null;
  expected_holding_days_max: number | null;
  signal_decay_hours: number | null;
  model_name: string;
  reason: string;
  risk_note: string;
  invalid_condition: string;
  follow_up_rule: string | null;
  status: string;
  reject_reason: string | null;
  valid_until: string;
  created_at: string;
  llm_provider: string | null;
  llm_model: string | null;
  llm_cost_usd: string | null;
}

export interface TradeRow {
  id: number;
  signal_id: number;
  symbol: string;
  market: string;
  direction: string;
  model_name: string;
  entry_time: string;
  entry_price: string;
  quantity: string;
  position_value: string;
  stop_loss_initial: string;
  stop_loss_current: string;
  target_1: string | null;
  target_2: string | null;
  trailing_stop_activated: boolean;
  exit_time: string | null;
  exit_price: string | null;
  exit_reason: string | null;
  pnl_amount: string | null;
  pnl_pct: string | null;
  realized_r_multiple: string | null;
  status: string;
}

export interface ReviewRow {
  id: number;
  trade_id: number;
  summary: string;
  entry_quality: number;
  exit_quality: number;
  risk_control_quality: number;
  what_worked: string[];
  what_failed: string[];
  model_adjustment_suggestion: string;
  should_keep_model_signal: boolean;
  llm_provider: string | null;
  llm_model: string | null;
  llm_cost_usd: string | null;
  created_at: string;
}

export interface StrategyModelRow {
  id: number;
  name: string;
  description: string;
  weight: string;
  is_active: boolean;
  auto_adjust_weight: boolean;
}

export interface ModelStatRow {
  id: number;
  model_name: string;
  window: string;
  trade_count: number;
  win_count: number;
  loss_count: number;
  win_rate: string | null;
  avg_win_pct: string | null;
  avg_loss_pct: string | null;
  profit_factor: string | null;
  expectancy: string | null;
  avg_r_multiple: string | null;
  sample_quality: 'INSUFFICIENT' | 'LOW' | 'ADEQUATE' | 'GOOD';
  last_computed_at: string;
}

export interface SystemHealthRow {
  id: number;
  job_name: string;
  started_at: string;
  finished_at: string | null;
  status: 'RUNNING' | 'SUCCESS' | 'FAILED';
  error_message: string | null;
  stats: Record<string, unknown>;
}

export interface DataFreshnessRow {
  symbol: string;
  timeframe: string;
  expected: string;
  actual: string | null;
  skew_minutes: number | null;
  status: 'FRESH' | 'STALE';
}

export interface LlmStatRow {
  day: string;
  purpose: string;
  total: number;
  cached_hits: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: string;
}

export interface RejectReasonRow {
  reason: string;
  n: number;
}

export interface EquityCurvePoint {
  timestamp: string;
  equity: string;
  cash: string;
}

export interface DrawdownPoint {
  timestamp: string;
  drawdown_pct: string;
}
