# Smart Appointment AI Agent 3.0

这是一个面向门店预约场景的多 Agent 智能助手。当前 3.0 架构已经从单一 workflow 演进为：

```text
用户输入
  -> Web / API Chat
  -> Session State Store（默认内存，可选 Redis）
  -> Understander Agent（意图理解）
  -> Supervisor Agent（计划、调度、完成判断）
      -> Consultation Agent
      -> Availability Agent
      -> Recommendation Agent
      -> Booking Agent
      -> Fallback Agent
  -> Response Writer Agent
  -> 最终回复
```

## 核心模块

- `agents/understander/`：意图理解 Agent，负责文本标准化、规则识别、上下文补全、低置信度 LLM fallback，并输出 `TaskFrame / RouteDecision`。
- `agents/supervisor/`：Supervisor Agent，负责把理解结果转成 `ExecutionPlan`，按计划调用 Specialist，接收结构化结果，并决定继续、等待用户、完成或失败。
- `agents/specialists/`：领域 Specialist Agents，目前包含咨询、排班、预约、推荐、兜底处理。
- `agents/response_writer/`：最终回复生成 Agent，统一消费 `execution_plan`、`turn_results`、`shared_focus_context`，避免多个子 Agent 分散回复。
- `agents/shared/`：跨 Agent 共享的状态、上下文、槽位和节点工具，不属于某个具体业务 Agent，但被多个 Agent 复用。
- `tools/`：稳定业务工具边界，封装知识库、排班、预约、技师、用户行为等服务调用。
- `services/` / `db/`：业务服务层和数据库访问层。
- `web/` / `api/`：Web 页面与 FastAPI 接口入口。

## 当前目录结构

```text
Smart-Appointment/
  app.py
  agents/
    understander/
    supervisor/
      planning/
      orchestration/
    specialists/
      consultation/
      availability/
      booking/
      recommendation/
      fallback/
    response_writer/
    shared/
  api/
  config/
  db/
  services/
  tools/
  web/
  tests/
  data/
```

## 状态模型

主链路使用 `SupervisorState` 保存会话状态，核心字段包括：

- `shared_focus_context`：跨 Agent 共享的关键上下文，例如服务项目、时间、时长、技师、性别偏好、手法偏好。
- `task_frame`：当前轮次的结构化任务语义，由 Understander Agent 生成。
- `execution_plan`：Supervisor 拥有的执行计划，记录当前任务、已完成任务、等待用户状态和完成原因。
- `turn_results`：当前轮次中各 Specialist 的结构化结果链。query-first 多步骤回复会从这里统一组合。
- `consultation` / `availability` / `booking` / `recommendation`：各领域 Agent 私有状态。
- `turn_trace` / `trace_history`：当前轮和历史轮次的可观测信息。
- `final_response`：Response Writer 生成的最终用户回复。

## 本地启动

当前仓库外层目录是 `2Smart-Appointment`，应用代码在内层 `Smart-Appointment`。请先进入应用目录：

```powershell
cd D:\graduate\wmluluResearch\3Agent\2Smart-Appointment\Smart-Appointment
```

如果项目里已经有 `.venv`，直接使用下面的最简启动命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

如果是第一次在新机器运行，先执行一次初始化：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

然后编辑 `.env`，至少配置可用的 LLM / Embedding key，再执行启动命令。

服务启动后访问：

```text
Web 首页:     http://127.0.0.1:8000/
API 文档:     http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json
```

也可以运行：

```powershell
.\.venv\Scripts\python.exe app.py
```

这种方式会使用 `app.py` 内置配置，服务地址是：

```text
http://127.0.0.1:8001/
```

## 启动排查

- 如果 PowerShell 提示 `python` 不存在，优先使用项目虚拟环境里的 `.\.venv\Scripts\python.exe`。
- 如果提示 `unable to open database file`，请确认当前目录是内层 `Smart-Appointment`，并确认 `data/` 目录可写；SQLite 默认数据库路径是 `data/smart_appointment.db`。
- 如果 `.env` 不存在，先从 `.env.example` 复制一份。
- 如果 LLM 调用失败，检查 `.env` 中的 `MODEL_PROVIDER`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`，以及 Embedding 相关配置。

## 常用测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\supervisor -q
.\.venv\Scripts\python.exe -m pytest tests\contract\graph -q
.\.venv\Scripts\python.exe -m pytest tests\contract\api\test_langgraph_api.py -q
```

如果 pytest 无法写入缓存或临时目录，可以指定临时目录：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit tests\contract -q --basetemp=$env:TEMP\sa_pytest_base
```

## LLM 开关

默认本地链路尽量保持确定性，以下 LLM 增强能力默认关闭：

```text
ENABLE_SUPERVISOR_LLM_PLANNER=false
ENABLE_SUPERVISOR_LLM_REVIEWER=false
ENABLE_RESPONSE_WRITER_LLM=false
```

打开这些开关后，Planner / Reviewer / Writer 可以调用 LLM，但输出仍会经过 Agent、Action allowlist 和 Booking guard 校验。

## 当前边界

- 主链路已经是 `Understander -> Supervisor Plan -> Specialist Agents -> Response Writer`。
- query-first 场景不再依赖旧的 `route_decision.continuation` 字段，而是由 `ExecutionPlan.tasks` 展开多步骤任务。
- 子 Agent 可以通过 `suggested_next_tasks` 提出下一步建议，但是否执行由 Supervisor 校验后决定。
- Booking Agent 是唯一可以推进预约确认、guard 和写库的业务 Agent。
- Recommendation Agent 可以做项目推荐、技师推荐、换一个、选择推荐承接，但不直接创建预约。
- Response Writer 统一组织最终回复，避免多个 Agent 各自输出用户可见文本。
