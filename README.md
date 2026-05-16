# Mini Hermes

> AI 模拟交易与策略验证系统 V2.0

一个轻量级的 AI 交易研究员,用于**验证交易模型**的模拟交易系统:观察美股 + BTC + ETH,
自动识别波段/趋势机会,生成结构化交易计划,在模拟账户中执行,自动止盈止损 + 复盘 + 模型评估。

**第一版边界**:不接实盘、不做真实下单。

## 核心原则

1. 先模拟、后实盘
2. 先风控、后收益(风控有交易否决权)
3. 所有交易信号必须结构化(JSON Schema 强约束)
4. 每个交易计划必须有 `invalid_condition`
5. 所有指标基于已收线 K 线(`is_final=True`)
6. 所有时间戳 UTC,价格明确复权
7. AI 必须能"承认不知道"(NO_TRADE / INSUFFICIENT_DATA)

## 技术栈

- **后端**:Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + APScheduler
- **数据库**:PostgreSQL 16 + TimescaleDB
- **前端**:Next.js 14 + TypeScript + Tailwind + shadcn/ui
- **LLM**:Anthropic / OpenAI(Structured Outputs + Pydantic 双层校验)
- **指标**:pandas-ta + pandas_market_calendars

## 快速开始

```bash
# 1. 启动 PostgreSQL + TimescaleDB + Redis
docker compose up -d db redis

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env,填入 ALPACA / LLM key(可选)

# 3. 启动后端
cd backend
pip install -e ".[dev]"
alembic revision --autogenerate -m "init"
alembic upgrade head
uvicorn app.main:app --reload

# 4. 访问
# API:        http://localhost:8000
# OpenAPI:    http://localhost:8000/docs
# 健康检查:    http://localhost:8000/health
```

## 当前状态(Step 1)

已完成:
- 13 个 SQLAlchemy 模型(Asset / Candle / IndicatorSnapshot / MarketRegime /
  Signal / Trade / Position / PortfolioSnapshot / Review / StrategyModel /
  ModelStat / SystemHealth / LlmCallLog)
- Pydantic SignalPlan / SignalPlanInput / RiskDecision schema 校验
- FastAPI 路由骨架(9 个 router)
- Asset CRUD 完整可用
- Alembic 迁移配置

待完成(按 Step 顺序):
- Step 2: 行情采集(Alpaca,复权 / UTC / is_final)
- Step 3: 指标计算
- Step 4: 三个策略评分模型
- Step 5: MarketRegime 分类
- Step 6: 风控引擎
- Step 7: 模拟交易引擎
- Step 8: 信号生成(纯规则版)
- Step 9: LLM 接入
- Step 10: 复盘 + ModelStat
- Step 11: Next.js 前端
- Step 12: SystemHealth + heartbeat

## 文档

完整 spec V2.0 见 `docs/spec.md`(待添加)。
