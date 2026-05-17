# Mini Hermes V2.0

> AI 模拟交易与策略验证系统

一个轻量级 AI 交易研究员,用于**验证交易模型**的模拟交易系统:观察美股 + BTC + ETH,
自动识别波段/趋势机会,生成结构化交易计划,在模拟账户中执行,自动止盈止损 + 复盘 + 模型评估。

**第一版边界**:不接实盘、不做真实下单。

## 核心原则

1. 先模拟、后实盘
2. 先风控、后收益(风控有交易否决权)
3. 所有交易信号必须结构化(JSON Schema 强约束)
4. 每个交易计划必须有 `invalid_condition`
5. 所有指标基于已收线 K 线(`is_final=True`)
6. 所有时间戳 UTC,价格明确复权 (SPLIT_ADJUSTED)
7. AI 必须能"承认不知道"(NO_TRADE / INSUFFICIENT_DATA)

## 状态

V1 完整闭环已搭建。Step 1-12 全部完成。

## 技术栈

- **后端**:Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + APScheduler
- **数据库**:PostgreSQL 16 + TimescaleDB
- **前端**:Next.js 15 + React 19 + TypeScript + Tailwind + SWR
- **LLM**:Anthropic / OpenAI (Structured Outputs + Pydantic 双层校验)
- **指标**:pandas + pandas-ta + pandas_market_calendars

## 已实现功能

| Step | 模块 | 状态 |
|------|------|------|
| 1 | 后端骨架 + 13 个 ORM 模型 + Alembic + Asset CRUD | ✓ |
| 2 | 行情采集(Alpaca + yfinance fallback,SPLIT_ADJUSTED + UTC + is_final) | ✓ |
| 3 | 指标计算(MA/EMA/RSI/MACD/ATR/支撑压力/布林,仅已收线) | ✓ |
| 4 | 三个策略评分模型(TrendBreakout / PullbackTrend / MovingAverageTrend) | ✓ |
| 5 | 市场环境分类(6 种 regime,基于 SPY + VIX + BTC) | ✓ |
| 6 | 风控引擎(13 项检查 + 4 个相关性组) | ✓ |
| 7 | 模拟交易引擎(fill_policy / 跳空 / 同 bar SL+TP / 移动止损 / R Multiple) | ✓ |
| 8 | 信号生成纯规则版 + pending 重过滤 + supersede 旧信号 | ✓ |
| 9 | LLM 接入(Anthropic / OpenAI) + input_hash 缓存 + 失败降级到规则 | ✓ |
| 10 | Review + ModelStat(8 项指标) + 自动权重调整 | ✓ |
| 11 | Next.js 前端 8 页(暗色主题) | ✓ |
| 12 | SystemHealth heartbeat + APScheduler + /system 页 | ✓ |

## 8 个前端页面

- `/` - Dashboard(账户净值、回撤、最近信号、市场环境)
- `/watchlist` - 观察池
- `/signals` - 信号(状态过滤 + 触发生成,SSE 实时进度)
- `/positions` - 持仓
- `/trades` - 历史交易(P&L / R Multiple)
- `/models` - 策略模型 + 30 天表现统计
- `/reviews` - 复盘(LLM/规则两版)
- `/llm` - **LLM 调用日志** (prompt / 输入 / 思考 / 原始响应,新增)
- `/llm/decision` - **LLM 实时调试** (单标的流式跑决策,新增)
- `/system` - 系统健康度(任务运行 / 数据新鲜度 / LLM 成本 / 风控拒绝 Top)

## V2.1 性能 / LLM 透明度改造

本分支(`feat/perf-llm-visibility`)的核心改进:

- **卡顿修复**
  - 全局 `<SWRConfig>` (dedupe 5s, 不在 focus 时刷新, keepPreviousData 防闪烁)
  - 各页面 polling 30s → 60-120s
  - `SignalOut` 拆为 `SignalListItem` (轻) + `SignalDetail` (全),列表 payload 缩 80%
  - 长列表服务端分页 `limit=50` 默认,加上下页按钮
  - `POST /api/signals/run` 改 `BackgroundTasks` + 立即返回 `job_id`,不再阻塞 UI
  - `ai_composite.combine` N+1 修复(一次 IN 查询替代 9 次)
  - `/api/system/data-freshness` 一次 GROUP BY 查询替代 22×3=66 次
  - `CandleChart` `React.memo` + 父组件 `useMemo` 记忆 markers/priceLines

- **LLM 思考可见**
  - `LlmCallLog` 新增 `system_prompt` / `user_input` / `raw_response_text` / `thinking` / `attempts` 列
  - `Signal` / `Review` 新增 `llm_call_log_id` FK,可从信号详情直接跳到完整调用记录
  - `llm_client` 默认对兼容模型开启 Anthropic extended thinking,捕获 `ThinkingBlock`
  - 新增 SSE 端点:
    - `GET /api/llm/stream/run-signals/{job_id}` - 后台运行的实时进度 + 当前资产 thinking
    - `GET /api/llm/stream/decision/{symbol}` - 单标的实时跑评分 + LLM 决策(不开仓)
  - 新增 REST 端点:
    - `GET /api/system/llm-logs` - 列表
    - `GET /api/system/llm-logs/{id}` - 详情(含 prompt / 输入 / 思考 / 原始响应)
  - 前端新增 `/llm` 日志页 + `/llm/[id]` 详情页 + `/llm/decision` 实时调试页

应用迁移:

```bash
cd backend
alembic upgrade head     # 应用 20260518_llm_visibility 迁移
```

## 快速开始

```bash
# 1. 启动 PostgreSQL + TimescaleDB + Redis
docker compose up -d db redis

# 2. 配置 env
cp .env.example .env
# 编辑 .env: 填 ALPACA / ANTHROPIC key(可选,无 key 仍能用 yfinance + 规则模式)
# 设置 ENABLE_LLM_DECISION=false 跑纯规则模式

# 3. 后端
cd backend
pip install -e ".[dev]"
alembic revision --autogenerate -m "init"
alembic upgrade head
uvicorn app.main:app --reload     # API: http://localhost:8000
python -m app.scheduler           # 在另一个终端跑调度器

# 4. 前端
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

## 命令

```bash
# 后端
uvicorn app.main:app --reload         # API
python -m app.scheduler               # 调度器
pytest                                # 测试

# 数据库
alembic revision --autogenerate -m "..."
alembic upgrade head

# 前端
npm run dev / build / start
```

## 目录结构

```
mini-hermes/
  backend/
    app/
      api/             # 9 个 router
      models/          # 13 个 SQLAlchemy 模型
      schemas/         # Pydantic
      services/        # data / indicator / market_regime /
                       # risk / paper_trading / decision /
                       # narration / model_weight / llm_client
      strategies/      # 3 个策略 + AI Composite
      jobs/            # 9 个定时任务 + helper
      utils/           # time_utils / logging_utils
      main.py
      scheduler.py
    alembic/
    tests/
    Dockerfile
  frontend/
    app/               # Next.js App Router
      page.tsx (Dashboard)
      watchlist / signals / positions / trades /
      models / reviews / system /
    Dockerfile
  docker-compose.yml
  .env.example
```

## 核心闭环(spec 第 4 章)

```
行情采集 (is_final=True)
  → 指标计算 (基于已收线)
  → 市场环境分类
  → 策略评分 × 3
  → AI Composite (应用 model_weight)
  → SignalPlan (LLM 或规则)
  → JSON Schema + Pydantic 双层校验
  → 风控过滤 (含 pending 重过滤 + 相关性组)
  → 模拟交易开仓 (明确 fill_policy)
  → 持仓追踪 (MFE / MAE / 移动止损)
  → 自动平仓 (SL / TP / max_holding / AI 风险退出)
  → 复盘 (LLM / 规则)
  → ModelStat (expectancy / profit_factor / sample_quality)
  → 模型权重自动调整
```

## 安全保证

- API Key:仅从 env 读取,从不进入 prompt / log / trace
- LLM 输出:JSON Schema (Pydantic) 双层校验,失败降级到规则
- 风控:13 项 + 相关性组,任一不通过即拒绝
- 时间:全 UTC,K 线 is_final 严格,absolutely no future-function
- 信号生命周期:7 个状态,过期自动清理
- 任务隔离:每个 job 独立 SystemHealth 记录,任一失败不影响其他

## 风险声明

Mini Hermes 用于交易研究、模拟交易和策略验证,**不构成投资建议**。

任何交易模型都可能失效,AI 生成的点位、信号和判断只能作为研究对象,不能保证盈利。

第一版**不应接入实盘账户、不应使用杠杆、不应执行真实资金交易**。
