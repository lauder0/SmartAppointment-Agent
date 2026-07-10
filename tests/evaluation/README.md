# SmartAppointment-Agent 评测集

这套评测集用于检查当前系统在 LangGraph + tool 实现下，是否能稳定完成真实多轮预约咨询任务。它不是单纯问答样例，而是覆盖上下文、状态、工具调用和业务动作的回归评测。

## 覆盖维度

- 静态咨询：服务项目、价格、营业时间、地址、会员政策、预约规则。
- 实时排班：按时间、时长、性别、指定技师、手法偏好筛选可约技师。
- 预约草稿：多轮补齐时间、项目、时长、性别、技师和偏好。
- 确认机制：预约信息完整后先确认，不直接写库。
- 上下文管理：排班补充、预约补全、待确认状态、临时咨询、礼貌结束。
- 意图转换：咨询到预约、排班到预约、预约中临时咨询。
- 鲁棒性：口语化、混合表达、寒暄、感谢、空输入、模糊业务表达。
- 安全边界：无关请求不应进入预约或工具调用。

## 文件说明

- `conversation_regression_cases.json`：真实对话回归评测。偏向用户体验、口语表达、多轮上下文和回复内容检查；每个 case 使用独立 session，避免上下文串扰。
- `state_contract_cases.json`：状态契约评测。偏向 `route_decision`、`booking`、`focus_context`、`availability_result` 等结构化状态断言。
- `rag_retrieval_cases.json`：知识库检索评测。偏向 RAG 文档召回质量。
- `run_eval.py`：轻量运行器，直接调用 `api.chat_handler.ProcessUserInput_stream`，也就是 Web UI 当前使用的聊天入口。

## 用例结构

每个 case 包含：

- `id`：稳定用例编号。
- `category`：主意图类别，例如 `availability_query`、`context_management`。
- `tags`：覆盖维度标签，例如 `multi_turn`、`preference`、`confirmation_guard`。
- `side_effect`：是否可能创建预约或写入数据库。
- `turns`：多轮用户输入和每轮预期。

每轮 `expect` 支持：

- `agent_label`：检查回复是否来自指定机器人，例如 `咨询机器人` 或 `预约机器人`。
- `route_action`：检查 `route_decision.action`，推荐新用例优先使用。
- `booking_status`：检查 `booking.status`，推荐新用例优先使用。
- `state_intent`：兼容旧用例，由新状态派生，不建议新用例继续增加。
- `state_pending_action`：兼容旧用例，由 `booking.status` 派生，不建议新用例继续增加。
- `state_equals`：按点路径检查 state 字段是否等于指定值。
- `state_contains`：按点路径检查 state 字段字符串中是否包含指定文本。
- `state_not_equals`：按点路径检查 state 字段不能等于指定值。
- `state_list_min_length`：检查列表字段长度下限。
- `state_path_exists`：检查字段路径存在。
- `must_include_all`：回复必须全部包含的文本。
- `must_include_any`：回复至少包含一个的文本。
- `must_not_include_any`：回复不能包含的文本。

## 指标

运行器会输出这些指标：

- `case_pass_rate`：用例级通过率。
- `turn_pass_rate`：对话轮次级通过率。
- `avg_turn_latency_ms`：平均每轮耗时。
- `p95_turn_latency_ms`：P95 每轮耗时。
- `By category`：按类别统计通过率。
- `By key tag`：按关键标签统计通过率。
- `Slowest turns`：最慢的若干轮，用于定位模型调用或工具调用瓶颈。

## 运行方式

列出全部用例：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --list
```

运行非写库用例：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py
```

运行状态契约评测：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --cases-file tests\\evaluation\\cases\\state_contract_cases.json
```

运行指定用例：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --case CTX004 --show-responses
```

按类别运行：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --category context_management
```

按标签运行：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --tag preference
```

输出 JSON 报告：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --json-report output/eval_report.json
```

运行包含预约创建的用例：

```powershell
.\.venv\Scripts\python.exe tests\\evaluation\\runners\\run_eval.py --include-side-effects
```

## 评测建议

日常开发优先跑非写库用例，用来验证意图分类、上下文继承、实时排班查询、预约草稿和异常兜底。修改预约创建、推荐确认、数据库写入相关逻辑时，再单独打开 `--include-side-effects`。

预约时间窗口、营业时间和写库前 guard 这类强业务约束，优先使用 `tests/test_graph_node_contracts.py` 做确定性节点契约测试；对话评测只补充流畅性和上下文回归。

如果某个 case 失败，优先查看三类信息：模型是否把意图分类错了，state 是否继承或覆盖了错误字段，以及 tool 返回值是否和预期业务规则一致。
