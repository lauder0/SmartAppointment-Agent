# Smart Appointment 成熟 Agent 分层建设框架

本文档用于指导 Smart Appointment 3.0 从“功能可用”逐步演进为“成熟 Agent 工程项目”。框架结合当前项目实现、《成熟 Agent 项目建设指南.md》、`goal.md` 中的能力目标，以及 Agent 工程实践经验整理而成。

核心思路是：不要只按技术模块拆项目，而要按 **Agent 的完整运行链路 + 工程治理能力** 来拆。每一层都应该回答三个问题：

- 这一层负责什么？
- 当前项目已经做到什么？
- 下一步应该补什么？

推荐将项目拆成 15 个层次：

```text
0. 业务目标与成功指标层
   ↓
1. 用户入口与交互体验层
   ↓
2. 意图理解与任务建模层
   ↓
3. 对话上下文与槽位管理层
   ↓
4. Agent 编排与任务流转层
   ↓
5. 领域 Agent / Specialist 能力层
   ↓
6. 工具调用与业务服务层
   ↓
7. 知识库与 RAG 层
   ↓
8. 记忆与状态持久化层
   ↓
9. Prompt 与上下文工程层
   ↓
10. 安全、权限与 Guardrail 层
   ↓
11. 稳定性、异常恢复与幂等层
   ↓
12. 可观测、日志与 Trace 层
   ↓
13. 评测、实验与持续迭代层
   ↓
14. 部署、运维与成本治理层
```

---

## 0. 业务目标与成功指标层

这一层是所有 Agent 项目的地基。

核心问题：

```text
这个 Agent 到底解决什么业务问题？
什么叫做做得好？
什么叫做失败？
```

对 Smart Appointment 来说，业务目标不是“做一个聊天机器人”，而是：

```text
面向按摩门店的智能预约 Agent，
能完成服务咨询、技师推荐、排班查询、预约创建、用户偏好沉淀与复用。
```

建议定义以下指标：

- **任务成功率**：用户从咨询到成功完成目标任务的比例。
- **预约转化率**：用户咨询服务后进入预约确认或成功预约的比例。
- **推荐接受率**：推荐技师后用户接受推荐的比例。
- **多轮完成率**：跨多轮补槽后仍能完成任务的比例。
- **错误预约率**：时间、项目、技师、时长错误的比例。
- **人工介入率**：需要人工处理的比例。
- **平均完成轮次**：完成一次预约平均需要几轮对话。
- **响应延迟与成本**：P95 延迟、LLM token 成本、工具调用成本。

当前项目后续可以将这些内容整理为 `PROJECT_GOAL.md`，或补充到 README 的项目目标部分。

---

## 1. 用户入口与交互体验层

这一层负责用户如何进入系统、如何和 Agent 对话、如何感知任务进度。

当前项目已经具备：

```text
Web 页面
/chat
/chat/stream
/chat/reset
知识库、技师、排班、用户行为等管理页面
```

成熟项目应关注：

- 多端入口：Web、移动端、小程序、客服后台、API。
- 流式输出：用户能看到 Agent 正在处理。
- 会话恢复：刷新页面或重新进入后能恢复上下文。
- 明确反馈：查询中、推荐中、待确认、预约成功、失败原因。
- 用户可控：允许取消、修改、重新推荐、重置会话。
- 管理后台：配置项目、技师、排班、知识、用户偏好。

对当前项目，建议下一步补充：

```text
用户侧：展示当前预约草稿状态
管理侧：展示每次 Agent 路由链路和工具调用结果
```

---

## 2. 意图理解与任务建模层

这一层负责理解用户真正想完成什么任务，而不是只做简单 intent 分类。

例如用户说：

```text
我想做全身推拿，你有推荐的技师吗
```

这句话同时包含：

- 服务选择：`全身推拿`
- 推荐请求：`推荐技师`

成熟系统应将其建模为：

```json
{
  "primary_intent": "recommend_technician",
  "secondary_intents": ["service_selection"],
  "task_type": "recommendation_before_booking",
  "slots": {
    "service_type": "全身推拿"
  },
  "missing_slots": ["start_time"],
  "next_action": "ask_time_for_recommendation"
}
```

这一层建议拆成以下能力：

- **意图识别**：咨询、查排班、预约、推荐、修改、取消、闲聊、越界请求。
- **复合意图识别**：服务选择 + 推荐、查时间 + 指定技师、预约 + 偏好。
- **任务类型建模**：咨询任务、排班任务、推荐任务、预约任务、售后/修改任务。
- **槽位抽取**：项目、时间、时长、技师、性别偏好、手法偏好、用户身份。
- **任务优先级**：当一句话里有多个意图时，判断哪个是主链路。
- **置信度与兜底**：低置信度时追问，而不是硬路由。

这一层是当前项目后续重点优化方向之一，因为它决定整个 Agent 链路是否自然。

---

## 3. 对话上下文与槽位管理层

这一层负责记录用户已经说过什么、当前任务还缺什么、下一轮应该问什么。

它和意图理解不同：

- 意图理解回答：用户想做什么。
- 槽位管理回答：完成这个任务还差什么信息。

对预约项目来说，核心槽位包括：

```text
service_type       项目
start_time         开始时间
duration_minutes   时长
technician_id      技师 ID
technician_name    技师姓名
gender_preference  性别偏好
style_preference   手法偏好
user_id            用户
confirmation       是否确认
```

成熟设计需要支持：

- 多轮补槽。
- 用户修改已填槽位。
- 用户中途插入咨询问题。
- 查询推荐时保留 pending intent。
- 从上一轮服务目录继承 service_type。
- 从推荐结果继承 technician_id。
- 从历史偏好补默认值，但不能偷偷替用户确认。

建议抽象为 `Task Frame / Dialogue Frame`：

```json
{
  "task_id": "booking_20260712_xxx",
  "task_type": "recommendation_before_booking",
  "status": "collecting_slots",
  "collected_slots": {
    "service_type": "全身推拿"
  },
  "missing_slots": ["start_time"],
  "pending_next": "query_availability_for_recommendation"
}
```

这样比单纯依赖对话历史更加稳定。

---

## 4. Agent 编排与任务流转层

这一层决定多个 Agent 如何协作。

当前 3.0 已经采用：

```text
Supervisor
  -> Consultation Agent
  -> Availability Agent
  -> Booking Agent
  -> Recommendation Agent
  -> Fallback Handler
```

成熟项目里，编排层需要明确：

- 谁负责路由。
- 谁负责状态初始化。
- 谁负责跨 Agent handoff。
- 谁能结束任务。
- 哪些操作必须用户确认。
- 哪些 Agent 可以连续执行。
- 哪些 Agent 只能被动触发，不能主动接管。
- 失败后回到哪个节点。

当前项目理想链路示例：

```text
服务咨询
  -> 用户选择项目并要求推荐
  -> Supervisor 识别 recommendation_before_booking
  -> Availability 查询可约候选人
  -> Recommendation 排序和解释
  -> 用户接受
  -> Booking 生成确认单
  -> 用户确认
  -> Booking Guard
  -> 创建预约
```

建议后续补充正式架构图：

```text
Supervisor Router
  ├─ Consultation Flow
  ├─ Availability Flow
  ├─ Recommendation Flow
  │    └─ accepted -> Booking Flow
  ├─ Booking Flow
  │    ├─ slot filling
  │    ├─ confirmation
  │    ├─ guard
  │    └─ transaction create
  └─ Fallback Flow
```

---

## 5. 领域 Agent / Specialist 能力层

这一层将业务能力按领域拆分。

建议当前项目固定为 5 个核心 Specialist。

### Consultation Agent

负责：

- 服务项目咨询。
- 价格咨询。
- 营业时间。
- 地址。
- 会员规则。
- 预约规则。
- 注意事项。

### Availability Agent

负责：

- 解析时间。
- 查询排班。
- 筛选可约技师。
- 返回候选时段。
- 给推荐或预约提供候选池。

### Recommendation Agent

负责：

- 根据服务类型、用户偏好、历史行为、可约候选人排序。
- 解释推荐理由。
- 支持“换一个”。
- 支持“为什么推荐他”。
- 不直接创建预约，只把推荐结果交给 Booking。

### Booking Agent

负责：

- 预约草稿。
- 槽位补全。
- 待确认摘要。
- 用户确认解析。
- guard 检查。
- 幂等创建预约。
- 行为记录。
- 完成通知。

### Fallback / Recovery Agent

负责：

- 意图不清追问。
- 闲聊礼貌回复。
- 越界请求拒绝。
- 异常恢复。
- 引导用户回到主任务。

成熟项目里，每个 Specialist 都建议有：

```text
state.py      私有状态
nodes.py      节点
actions.py    业务动作
graph.py      子图入口
tests/        单测/契约测试
eval cases    多轮样例
```

当前 3.0 已经比较接近这个结构。

---

## 6. 工具调用与业务服务层

这一层负责 Agent 如何调用真实业务能力。

当前项目已经具备：

```text
tools/
services/
db/
repositories/
```

成熟项目中，工具不能只是函数，而应该是稳定协议。每个工具建议定义：

```json
{
  "name": "search_available_technicians",
  "description": "查询指定服务、时间和时长下可约技师",
  "input_schema": {},
  "output_schema": {},
  "permission": "read",
  "timeout_ms": 3000,
  "retryable": true,
  "idempotent": true,
  "risk_level": "low"
}
```

工具层要重点治理：

- 参数 schema。
- 返回结构标准化。
- 错误码。
- 超时。
- 重试。
- 幂等。
- 权限。
- mock 测试。
- 调用日志。
- 高风险工具确认。

建议将工具分为三类：

```text
只读工具：
- 查询服务项目
- 查询技师
- 查询排班
- 检索知识库
- 查询用户偏好

写入工具：
- 创建预约
- 修改预约
- 取消预约
- 记录用户行为
- 更新偏好

高风险工具：
- 创建正式预约
- 取消预约
- 修改关键业务数据
```

预约创建工具必须具备：

```text
confirmation_required = true
idempotency_key
guard_check
audit_log
```

---

## 7. 知识库与 RAG 层

这一层负责非结构化知识问答。

对当前项目，RAG 适合处理：

- 服务说明。
- 门店介绍。
- 会员规则。
- 注意事项。
- 价格政策。
- FAQ。
- 健康/按摩相关知识。

不适合只依赖 RAG 处理：

- 实时排班。
- 实时价格库存。
- 预约创建。
- 用户订单状态。
- 技师是否可约。

这些应走数据库或业务 API。

成熟 RAG 链路建议：

```text
知识源
  -> 文档解析
  -> 清洗
  -> 分块
  -> 元数据标注
  -> Embedding
  -> 向量索引 / 关键词索引
  -> Query Rewrite
  -> Hybrid Retrieval
  -> Rerank
  -> Context Assembly
  -> Grounded Answer
  -> Citation / Evidence Check
```

当前项目后续可以补：

- 知识文档版本号。
- chunk 元数据：分类、来源、更新时间。
- 检索评测集。
- Recall@K / MRR / answer correctness。
- 低置信度时“不知道/建议联系门店”。

---

## 8. 记忆与状态持久化层

这一层要区分 **状态** 和 **记忆**。

### 状态

状态是当前任务进行到哪一步，必须强一致。

例如：

```text
当前正在预约
已选择全身推拿
缺少时间
正在等待用户确认
```

状态应存在 session store 或数据库中。

### 记忆

记忆是辅助个性化的信息，不应该直接替用户做决定。

例如：

```text
用户偏好女技师
用户经常约下午
用户喜欢力度大
用户过去常选赵敏
```

成熟项目里建议区分：

```text
短期记忆：当前会话上下文
任务状态：当前任务进度
长期记忆：跨会话用户偏好
行为记忆：用户历史预约/选择
摘要记忆：长对话压缩
检索记忆：向量化的历史事实
```

当前项目已有 session state、user behavior、preference recall。后续建议补：

- 用户可查看/修改/删除偏好。
- 记忆置信度。
- 记忆来源：用户明确说的、行为推断的、系统生成的。
- 记忆更新时间。
- 记忆召回评测。

---

## 9. Prompt 与上下文工程层

成熟项目不能只靠一个巨大的 prompt。

建议分成：

```text
System Prompt：全局角色、安全边界、业务原则
Router Prompt：意图识别与路由规则
Specialist Prompt：各 Agent 的领域规则
Tool Prompt：工具选择和参数生成规则
Response Prompt：回复格式和语气
Recovery Prompt：异常恢复和追问策略
Evaluation Prompt：评测 judge 标准
```

上下文工程要解决：

```text
哪些信息进入模型？
哪些信息绝对不能进？
哪些信息必须结构化？
哪些历史要裁剪？
工具结果怎么注入？
RAG 结果怎么引用？
状态和用户输入怎么区分？
```

建议设计统一的 `ContextAssembler`：

```text
current_user_message
+ active_task_state
+ shared_focus_context
+ relevant_memory
+ retrieval_docs
+ recent_messages
+ business_rules
```

并为每个 Agent 设置自己的上下文预算。

---

## 10. 安全、权限与 Guardrail 层

Agent 项目成熟后必须有安全边界。

预约项目中的高风险动作包括：

- 创建预约。
- 修改预约。
- 取消预约。
- 记录用户偏好。
- 暴露用户历史行为。
- 修改知识库。
- 修改技师排班。

这一层要做：

- 工具权限控制。
- 用户身份校验。
- 高风险操作确认。
- Prompt injection 防护。
- RAG 内容不作为系统指令。
- 日志脱敏。
- 用户数据隔离。
- 管理端权限。
- 越权请求拒绝。
- 危险输入拦截。

当前项目的 Booking Guard 是一个好起点，后续可以扩展为统一 Guardrail：

```text
Before Tool Call Guard
After Tool Result Guard
Before Final Response Guard
Before Memory Write Guard
Before DB Write Guard
```

---

## 11. 稳定性、异常恢复与幂等层

这是从 Demo 到工程项目的关键分水岭。

成熟 Agent 必须处理：

- 模型超时。
- 模型输出格式错误。
- 工具调用失败。
- 排班结果为空。
- 数据库写入失败。
- 用户输入模糊。
- 用户中途切换话题。
- 重复确认。
- 重复创建预约。
- 多窗口并发请求。
- 状态丢失。
- 死循环。

建议建立统一失败分类：

```text
IntentError
SlotExtractionError
ToolTimeoutError
NoAvailabilityError
BookingConflictError
StateConflictError
LLMFormatError
PermissionDeniedError
```

对应恢复策略：

```text
retry       短暂失败重试
fallback    降级到规则/备用模型
clarify     向用户追问
confirm     高风险动作确认
rollback    失败回滚状态
terminate   循环或风险时终止
escalate    转人工
```

预约创建尤其需要幂等：

```text
idempotency_key = session_id + service_type + start_time + technician_id + user_id
```

避免用户重复点击“确认”导致重复预约。

---

## 12. 可观测、日志与 Trace 层

这一层回答：

```text
Agent 为什么这么回答？
它路由到了哪里？
调用了什么工具？
哪里失败了？
成本多少？
延迟多少？
```

成熟项目每次对话应有一条 trace：

```text
trace_id
session_id
user_id
message_id
router_decision
active_agent
slots_before
slots_after
tool_calls
rag_docs
model_name
prompt_version
latency_ms
token_usage
cost
final_response
error
```

对当前项目，尤其要记录：

- 用户输入。
- Supervisor 路由 action。
- route reason。
- active_agent。
- booking state。
- recommendation state。
- availability options。
- tool_results。
- final_response。

这样遇到 badcase 时可以直接定位：

```text
用户问推荐
但 router 选择了 start_or_continue_booking
原因是 service_catalog_selection
```

这就是可观测层的价值。

---

## 13. 评测、实验与持续迭代层

成熟 Agent 不能只靠手测。

当前项目已经有 `tests/evaluation`，这是很好的基础。建议继续分层评测：

```text
单轮意图识别评测
多轮任务链路评测
槽位抽取评测
工具调用参数评测
RAG 检索评测
推荐质量评测
预约安全评测
异常恢复评测
端到端对话回放评测
```

每个 badcase 都应该进入闭环：

```text
发现 badcase
  -> 归因：意图 / 槽位 / 编排 / 工具 / RAG / 记忆 / Prompt
  -> 修复
  -> 加入 eval case
  -> 回归测试
  -> 对比新旧版本
```

示例 badcase：

```text
case_name: service_selection_with_recommendation_request
expected_route:
  first: query_availability or ask_time_for_recommendation
  then: recommendation
not_expected:
  direct_booking_confirmation_without_recommendation_reason
```

这一层是项目持续成熟的核心。

---

## 14. 部署、运维与成本治理层

最后一层负责从“本地能跑”变成“稳定可上线”。

成熟项目要有：

- local / dev / staging / production 环境。
- 配置管理。
- 密钥管理。
- 数据库迁移。
- Redis / session store。
- RAG 索引版本。
- Prompt 版本。
- 模型版本。
- feature flag。
- 灰度发布。
- 回滚机制。
- 成本监控。
- 限流。
- 告警。
- 备份。

当前项目后续可以演进为：

```text
.env.example
config/settings.py
prompt_versions/
rag_index_versions/
eval_reports/
deployment/
docker-compose.yml
migration/
```

成本治理建议：

- Router 用小模型或规则优先。
- 复杂推荐再用大模型。
- RAG 检索限制 top_k。
- 对话历史压缩。
- 工具结果缓存。
- 避免重复查询排班。
- 限制最大 Agent 步数。

---

## Smart Appointment 总体分层图

```text
Smart Appointment Mature Agent Architecture

0. 业务目标与成功指标层
   - 预约转化率、任务成功率、推荐接受率、错误预约率

1. 用户入口与交互体验层
   - Web UI、Chat API、Streaming、管理后台

2. 意图理解与任务建模层
   - intent、复合意图、任务类型、优先级、置信度

3. 对话上下文与槽位管理层
   - service/time/duration/technician/preference/confirmation

4. Agent 编排与任务流转层
   - Supervisor、routing、handoff、task lifecycle

5. Specialist Agent 能力层
   - Consultation、Availability、Recommendation、Booking、Fallback

6. 工具调用与业务服务层
   - tools、services、repositories、schema、timeout、retry、idempotency

7. 知识库与 RAG 层
   - knowledge docs、embedding、retrieval、rerank、grounded answer

8. 记忆与状态持久化层
   - session state、task state、user preference、behavior memory

9. Prompt 与上下文工程层
   - router prompt、agent prompt、tool prompt、context assembly

10. 安全、权限与 Guardrail 层
   - confirmation、permission、PII、prompt injection、high-risk action guard

11. 稳定性、异常恢复与幂等层
   - retry、fallback、rollback、loop detection、booking idempotency

12. 可观测、日志与 Trace 层
   - trace_id、route_decision、tool_calls、latency、token、cost、error

13. 评测、实验与持续迭代层
   - unit、contract、e2e、eval、badcase、A/B、regression

14. 部署、运维与成本治理层
   - env、Redis、DB、Docker、monitoring、release、rollback、cost control
```

---

## 推荐完善优先级

不建议从 0 到 14 机械顺序推进，而应按成熟度路线推进。

### 第一阶段：把主链路做稳

```text
2. 意图理解与任务建模
3. 槽位管理
4. Agent 编排
5. Specialist 能力
6. 工具调用
11. 稳定性与幂等
```

目标：咨询、查排班、推荐、预约这条主链路稳定。

### 第二阶段：让项目可解释、可回归

```text
12. 可观测 Trace
13. 评测体系
9. Prompt 与上下文工程
```

目标：每个 badcase 都能定位和复现。

### 第三阶段：提升智能化和个性化

```text
7. RAG
8. 记忆
5. Recommendation Agent
```

目标：回答更准，推荐更像“懂用户”。

### 第四阶段：走向生产级

```text
10. 安全权限
14. 部署运维
0. 指标治理
1. 体验优化
```

目标：能上线、能监控、能灰度、能持续迭代。

---

## 当前项目成熟度判断

从当前 3.0 项目看，可以判断为：

```text
整体：Level 3 工程级雏形
局部：Agent 编排、状态、测试已经接近成熟项目结构
短板：意图复合建模、trace 可观测、安全治理、评测闭环、部署运维
```

已经比较好的地方：

- 有 Supervisor + Specialist 架构。
- 有 LangGraph 风格的状态流转。
- 有 consultation / availability / booking / recommendation 分包。
- 有 session state。
- 有 tools / services / db 分层。
- 有 unit / contract / e2e / evaluation。
- 有 RAG 和知识服务基础。
- 有预约 guard 和行为记录。

下一步最值得补的不是继续堆功能，而是：

```text
1. 把意图与任务建模抽象清楚
2. 把 trace 和 badcase 闭环补起来
3. 把工具 schema / 权限 / 幂等做统一
4. 把评测集覆盖到真实多轮链路
5. 把安全和部署治理补成体系
```

这样项目才能从“功能完整”走向“成熟 Agent 工程”。
