# Smart Appointment 3.0 澶氭櫤鑳戒綋鏀归€犳柟妗?
> 鏇存柊鏃堕棿锛?026-07-16  
> 鏈増瀹氫綅锛氭寜鐓ф渶鏂拌璁猴紝閲嶆柊璁捐涓衡€滄剰鍥剧悊瑙ｅ眰 -> Supervisor 璁″垝涓庡惊鐜?-> 瀛?Agent 鎵ц -> Response Writer 缁熶竴鍥炲鈥濈殑澶氭櫤鑳戒綋涓荤嚎銆?
## 0. 鏈鏇存柊鎽樿

鏈鏂规鐩稿鏃х増鍋氫簡鍑犲鍏抽敭璋冩暣锛?
- 灏?**Response Writer** 浠?Supervisor 鍐呴儴鑱岃矗涓崟鐙娊鍑猴紝浣滀负鏈€缁堝洖澶嶇粍缁囧眰銆?- 鏄庣‘ **Supervisor 涓嶅寘鍚畬鏁存剰鍥捐瘑鍒?*锛岃€屾槸娑堣垂鎰忓浘鐞嗚В灞備骇鍑虹殑 `TaskFrame` / `RouteDecision` 鍚庡埗瀹氳鍒掋€?- 鏄庣‘ Supervisor 鐨勬牳蹇冮棴鐜槸锛歚鍒跺畾璁″垝 -> 璋冪敤瀛?Agent -> 鎺ユ敹缁撴灉 -> 鍒ゆ柇缁х画/绛夊緟/缁撴潫/淇璁″垝`銆?- 鏄庣‘瀛?Agent 涓嶅啀鍐冲畾涓嬩竴姝ヨ矾鐢憋紝鍙繑鍥炵粨鏋勫寲缁撴灉鍜?`suggested_next_tasks`锛屼笅涓€姝ョ敱 Supervisor 鍒ゆ柇銆?- 灏?Recommendation Agent 鎵╁睍涓虹粺涓€鎺ㄨ崘 Agent锛屽悓鏃惰鐩?**椤圭洰鎺ㄨ崘** 鍜?**鎶€甯堟帹鑽?*銆?- 鏄庣‘褰撳墠浠ｇ爜閲岀殑 `consultation` Specialist 鍦ㄧ洰鏍囨灦鏋勪腑瀵瑰簲 **Knowledge Agent**锛屽悗缁彲閫愭閲嶅懡鍚嶆垨淇濈暀鍏煎鍛藉悕銆?
### 0.1 褰撳墠钀藉湴鐘舵€侊紙2026-07-16锛?
鏈疆宸插皢涓婚摼璺粠鈥渞oute_decision 鐩存帴椹卞姩 Specialist鈥濇帹杩涗负锛?
```text
Understanding
  -> deterministic ExecutionPlan
  -> Supervisor Controller
  -> Child Agent
  -> Supervisor Completion / Plan Review
  -> Response Writer
```

宸插畬鎴愶細

- `ExecutionPlan / PlanTask` 宸叉垚涓烘甯镐富閾捐矾鐨勬墽琛岄┍鍔紝`route_decision` 涓昏浣滀负鍏煎閫傞厤鍜?trace 瀛楁淇濈暀銆?- 鎵€鏈夊瓙 Agent 杩斿洖鍚庣粺涓€鍥炲埌 `supervisor_continue`锛岀敱 Supervisor 鏍囪浠诲姟鐘舵€併€侀€夋嫨涓嬩竴姝ユ垨缁撴潫銆?- `suggested_next_tasks` 宸叉垚涓哄瓙 Agent 寤鸿鍚庣画浠诲姟鐨勬爣鍑嗗瓧娈碉紱Supervisor 缁熶竴鏍￠獙骞跺皢閲囩撼/鎷掔粷鍘熷洜鍐欏叆 `execution_plan.suggested_task_reviews`銆?- `Recommendation Agent` 宸茶鐩栭」鐩帹鑽愬拰鎶€甯堟帹鑽愩€?- `Booking Agent` 宸查€氳繃 `booking_result.v1` 濂戠害閫忓嚭鍐欐搷浣溿€佸畨鍏ㄣ€佸箓绛夊拰鐢ㄦ埛绛夊緟鍔ㄤ綔銆?- `Response Writer` 宸茬嫭绔嬩负 `agents/response_writer/`锛岀粺涓€娑堣垂 `execution_plan + turn_results + shared_focus_context`銆?- `Trace` 宸茶ˉ鍏?execution plan銆乸lan review銆亀riter 鍜?turn_results 鎽樿銆?
浠嶅缓璁户缁寮猴細

- LLM Planner / Reviewer 宸叉寜鐧藉悕鍗曟帴鍏ヤ负鍙€夊寮猴紝榛樿鍏抽棴锛涘悗缁噸鐐规槸娌夋穩澶嶆潅澶氭剰鍥?badcase锛岄€愭鎵╁ぇ鍚敤鍦烘櫙銆?- `consultation` 鍛藉悕浠嶄綔涓?Knowledge Agent 鐨勫吋瀹瑰悕绉帮紝鍚庣画鍙粺涓€閲嶅懡鍚嶃€?- 鏍稿績鍗曞厓銆佸绾﹀拰绔埌绔祴璇曞凡閫氳繃锛涘悗缁户缁ˉ璇勬祴闆嗚鐩栧拰绠＄悊渚?Trace 灞曠ず銆?
## 1. 鏀归€犵洰鏍?
鐩爣鏄妸褰撳墠绯荤粺浠庘€滄剰鍥捐瘑鍒悗鐩存帴璺敱鍒?Specialist workflow鈥濈殑缁撴瀯锛屽崌绾т负鏇存竻鏅般€佹洿鍙В閲婄殑澶氭櫤鑳戒綋绯荤粺锛?
```text
鐢ㄦ埛杈撳叆
  -> 鎰忓浘鐞嗚В涓庝换鍔″缓妯″眰
  -> Supervisor 璁″垝涓庣紪鎺掑眰
  -> 瀛?Agent 鎵ц灞?  -> Supervisor 缁撴灉妫€鏌ヤ笌寰幆
  -> Response Writer 缁熶竴鍥炲灞?  -> 鐢ㄦ埛
```

鏍稿績鍙樺寲锛?
- **鎰忓浘鐞嗚В灞傜嫭绔?*锛氬彧璐熻矗涓夊眰鎰忓浘鐞嗚В銆佹Ы浣嶆娊鍙栥€佷笂涓嬫枃琛ュ己銆佷换鍔″缓妯★紝涓嶈礋璐ｆ墽琛屽拰澶氭缂栨帓銆?- **Supervisor 璐熻矗璁″垝鍜屽惊鐜?*锛氭牴鎹剰鍥剧悊瑙ｇ粨鏋滅敓鎴愭墽琛岃鍒掞紝璋冪敤瀛?Agent锛屾帴鏀剁粨鏋滐紝鍒ゆ柇鏄惁缁х画銆佺瓑寰呯敤鎴枫€佸け璐ユ仮澶嶆垨缁撴潫銆?- **瀛?Agent 璐熻矗棰嗗煙鎵ц**锛氶潤鎬佺煡璇嗘煡璇€佹帓鐝煡璇€佹帹鑽愩€侀绾﹀垎鍒敱鐙珛瀛?Agent 瀹屾垚銆?- **Response Writer 鍗曠嫭鎷嗗嚭**锛氭渶缁堣嚜鐒惰瑷€鍥炲鐢?Writer 鏍规嵁 Supervisor 鐨勮鍒掔姸鎬佸拰瀛?Agent 缁撴瀯鍖栫粨鏋滅粺涓€缁勭粐銆?- **Booking 淇濇寔纭畾鎬?*锛氭墍鏈夐绾﹀啓鎿嶄綔浠嶇敱纭畾鎬ф祦绋嬨€佺敤鎴风‘璁ゅ拰 Guard 鎺у埗锛屼笉鑳戒氦缁?LLM 鑷敱鍐崇瓥銆?
杩欏鏂规鐨勭洰鏍囦笉鏄姣忎釜瀛?Agent 閮藉彉鎴愬畬鍏ㄨ嚜鐢辩殑 LLM Tool Agent锛岃€屾槸鍏堝舰鎴愮ǔ瀹氱殑鈥滅悊瑙?-> 璁″垝 -> 鎵ц -> 妫€鏌?-> 鍥炲鈥濋棴鐜€?
---

## 2. 鐩爣鏋舵瀯

### 2.1 涓婚摼璺?
```text
User Message
  |
  v
Understanding Layer
  - Rule Understanding
  - Contextual Resolver
  - LLM Fallback
  - TaskFrame / RouteDecision / Slots
  |
  v
Supervisor
  - Planner: 鍒跺畾 ExecutionPlan
  - Controller: 鎸夎鍒掕皟鐢ㄥ瓙 Agent
  - Completion Checker: 鍒ゆ柇缁х画銆佺粨鏉熴€佺瓑寰呯敤鎴枫€佸け璐ユ仮澶?  - Plan Reviewer: 蹇呰鏃朵慨姝ｈ鍒?  |
  v
Child Agents
  - Knowledge Agent
  - Availability Agent
  - Recommendation Agent
  - Booking Agent
  |
  v
Response Writer
  - 鍩轰簬璁″垝鐘舵€佸拰 AgentResult 鐢熸垚鏈€缁堝洖澶?```

### 2.2 鎰忓浘鐞嗚В鍜?Supervisor 鐨勮竟鐣?
鎺ㄨ崘閲囩敤锛?
```text
鎰忓浘鐞嗚В灞?-> Supervisor -> Response Writer
```

涓嶅缓璁妸鎰忓浘鐞嗚В瀹屽叏濉炶繘 Supervisor 鍐呴儴銆傚師鍥犳槸锛?
- 鎰忓浘鐞嗚В姣忎釜鐢ㄦ埛鍥炲悎鍙渶瑕佸仛涓€娆★紝Supervisor 鐨勬墽琛屽惊鐜腑涓嶅簲璇ュ弽澶嶉噸鏂扮悊瑙ｅ師濮嬬敤鎴疯緭鍏ャ€?- Supervisor 鐨勬牳蹇冭亴璐ｆ槸鈥滄牴鎹凡缁忕悊瑙ｅソ鐨勪换鍔¤繘琛岃鍒掋€佽皟鐢ㄥ拰妫€鏌モ€濄€?- 杩欐牱杈圭晫鏇存竻妤氾細鐞嗚В灞備骇鍑轰换鍔¤涔夛紝Supervisor 浜у嚭鎵ц璁″垝锛學riter 浜у嚭鏈€缁堣〃杈俱€?
Supervisor 鍙互鍦ㄦ墽琛岃繃绋嬩腑鍙戠幇鈥滀俊鎭笉瓒斥€濇垨鈥滅粨鏋滀笉婊¤冻鐩爣鈥濓紝浣嗗畠涓嶉噸鏂板仛瀹屾暣鎰忓浘璇嗗埆锛岃€屾槸鐢熸垚 clarification銆佽ˉ鍏呬换鍔℃垨绛夊緟鐢ㄦ埛杈撳叆銆?
---

## 3. 褰撳墠瀹炵幇瀵圭収

### 3.1 褰撳墠宸茬粡鍏峰鐨勮兘鍔?
- `agents/understander/` 宸茬粡褰㈡垚涓夊眰鎰忓浘鐞嗚В缁撴瀯锛氳鍒欏眰銆佷笂涓嬫枃澧炲己銆丩LM 鍏滃簳銆?- `agents/supervisor/graph_builder.py` 宸茬粡鏈?Supervisor 鍥惧叆鍙ｅ拰澶氫釜 Specialist 瀛愬浘鑺傜偣銆?- `agents/supervisor/router_actions.py` 褰撳墠鎶?Supervisor router 璁捐寰楀緢钖勶紝瀹為檯鐞嗚В閫昏緫鍦?`agents.understander`銆?- `agents/supervisor/response_node.py` 宸茬粡鏄粺涓€鍑哄彛锛屼細璇诲彇 `turn_results` 骞剁敓鎴愭渶缁堝搷搴斻€?- `agents/specialists/result_contract.py` 宸叉湁閫氱敤 `SpecialistResult`銆乣suggested_next_tasks`銆乣turn_results`銆?- `Booking` 宸茬粡鏈?`booking/result_contract.py`锛屽啓鎿嶄綔閾捐矾鐩稿纭畾銆?- `Availability -> Recommendation` 鍜?query-first 鍦烘櫙宸茬粡鏈?continuation / suggested_next_tasks 杩囨浮閫昏緫銆?
### 3.2 褰撳墠涓昏宸窛

- LLM Planner / Plan Reviewer 宸插畬鎴愬彈鎺у彲閫夋帴鍏ワ紝褰撳墠榛樿鍏抽棴锛涢渶瑕佺户缁敤澶嶆潅澶氭剰鍥捐瘎娴嬮泦楠岃瘉寮€鍚悗鐨勬敹鐩娿€?- `consultation` Specialist 浠嶆壙鎷?Knowledge Agent 鑱岃矗锛屽懡鍚嶄笂杩樻湭瀹屽叏缁熶竴銆?- 瀛?Agent 缁撴灉宸茬粡缁熶竴杩涘叆 `SpecialistResult`锛屼絾鍚?Agent 鐨?facts 绮掑害杩樺彲缁х画鏍囧噯鍖栥€?- 宸ュ叿璋冪敤 registry 宸茶鐩栨牳蹇冭鍐欏伐鍏凤紝浣嗘帹鑽愭湇鍔°€乄riter銆丷eviewer 鐨勮皟鐢ㄨ娴嬭繕鍙户缁粏鍖栥€?- 闇€瑕佺户缁ˉ鍏呰瘎娴嬮泦銆佺鍒扮鎵嬪伐楠屾敹鍜岀鐞嗕晶 Trace 鍙鍖栥€?
---

## 4. 鍒嗗眰鑱岃矗璁捐

### 4.1 鎰忓浘鐞嗚В涓庝换鍔″缓妯″眰

鑱岃矗锛?
- 浣跨敤瑙勫垯灞傝瘑鍒‘瀹氭€ф剰鍥撅細鍜ㄨ銆佹帓鐝€佹帹鑽愩€侀绾︺€佺‘璁ゃ€佷慨鏀广€佸彇娑堛€佷笂涓嬫枃鎿嶄綔绛夈€?- 浣跨敤涓婁笅鏂囧寮鸿В鍐崇渷鐣ャ€佹寚浠ｅ拰鎵挎帴鍏崇郴锛屼緥濡傗€滃氨浠栧惂鈥濃€滄崲涓€涓€濃€滄槑澶╀笅鍗堜笁鐐瑰幓鈥濄€?- 浣跨敤 LLM 鍏滃簳澶勭悊瑙勫垯鍜屼笂涓嬫枃浠嶆棤娉曠ǔ瀹氳瘑鍒殑琛ㄨ揪銆?- 杈撳嚭缁熶竴浠诲姟璇箟锛屼緵 Supervisor 鍒跺畾璁″垝銆?
杈撳嚭瀵硅薄锛?
```python
TaskFrame = {
    "task_type": "knowledge_consultation | availability_query | service_recommendation | technician_recommendation | booking_creation | booking_confirmation | ...",
    "primary_intent": "...",
    "secondary_intents": [],
    "slots": {
        "service_type": None,
        "start_time": None,
        "duration_minutes": None,
        "technician_name": None,
        "preference": None,
    },
    "missing_slots": [],
    "context_links": [],
    "confidence": 0.0,
    "source": "rule | context | llm"
}
```

娉ㄦ剰锛?
- 杩欓噷鍙互缁х画淇濈暀 `RouteDecision` 浣滀负鍏煎瀛楁銆?- 鍚庣画涓婚€昏緫搴旈€愭浠?`route_decision.action` 杩佺Щ鍒?`ExecutionPlan.tasks`銆?
### 4.2 Supervisor 璁″垝涓庣紪鎺掑眰

鑱岃矗锛?
- 鎺ユ敹 `TaskFrame` / `RouteDecision` / 褰撳墠浼氳瘽鐘舵€併€?- 鐢熸垚 `ExecutionPlan`銆?- 鎸夎鍒掗€夋嫨涓嬩竴涓?`PlanTask`銆?- 璋冪敤瀵瑰簲瀛?Agent銆?- 鎺ユ敹瀛?Agent 鐨?`AgentResult`銆?- 鍒ゆ柇璁″垝鏄惁瀹屾垚銆佹槸鍚︾户缁€佹槸鍚︾瓑寰呯敤鎴枫€佹槸鍚﹀け璐ユ仮澶嶃€?- 蹇呰鏃朵慨姝ｈ鍒掞紝浣嗕笉鐩存帴鎵ц棰嗗煙宸ュ叿銆?
Supervisor 鎺ㄨ崘鎷嗘垚 4 涓ā鍧楋細

```text
agents/supervisor/
  plan_schema.py      # ExecutionPlan / PlanTask / PlanStatus
  planner.py          # TaskFrame -> ExecutionPlan
  controller.py       # next task selection, route adaptation, result writeback
  completion.py       # continue / waiting_user / completed / blocked / failed
```

Supervisor 涓嶈礋璐ｏ細

- 涓嶇洿鎺ユ煡鏁版嵁搴撱€?- 涓嶇洿鎺ュ垱寤洪绾︺€?- 涓嶇洿鎺ョ敓鎴愭渶缁堣嚜鐒惰瑷€闀垮洖澶嶃€?- 涓嶈 LLM 缁曡繃 Booking 纭鍜?Guard銆?- 涓嶉噰绾冲瓙 Agent 鐨勨€滀笅涓€姝ヨ矾鐢卞喅瀹氣€濓紝鍙噰绾崇粨鏋勫寲浜嬪疄鍜屽缓璁€?
### 4.3 瀛?Agent 鎵ц灞?
鏈」鐩缓璁厛淇濈暀鍥涗釜鏍稿績瀛?Agent銆?
#### Knowledge Agent

鑱岃矗锛?
- 鍥炵瓟闈欐€佺煡璇嗙被闂锛氭湇鍔￠」鐩€佷环鏍笺€佹椂闀裤€佸湴鍧€銆佽惀涓氭椂闂淬€佹敞鎰忎簨椤圭瓑銆?- 鎵ц RAG / 鐭ヨ瘑搴撴绱€?- 涓?Recommendation Agent 鎻愪緵鏈嶅姟椤圭洰浜嬪疄锛屼絾涓嶈礋璐ｆ渶缁堚€滄帹鑽愬喅绛栤€濄€?
鏄惁闇€瑕?LLM锛?
- 绠€鍗曟湇鍔＄洰褰曘€佷环鏍笺€佽惀涓氭椂闂村彲浠ユā鏉垮寲鍥炵瓟銆?- 寮€鏀惧紡鐭ヨ瘑闂瓟鍙互浣跨敤 RAG + LLM 缁勭粐绛旀銆?
杈撳嚭锛?
```python
knowledge_result.v1 = {
    "agent_name": "knowledge",
    "status": "completed | waiting_user | failed",
    "result_type": "knowledge_answer | service_catalog | service_detail",
    "facts": {
        "answer": "...",
        "documents": [],
        "service_items": []
    },
    "requires_user_input": False
}
```

#### Availability Agent

鑱岃矗锛?
- 鏍规嵁鏃堕棿銆侀」鐩€佹椂闀裤€佹妧甯堝亸濂芥煡璇㈠疄鏃舵帓鐝€?- 杩斿洖鍙害鎶€甯堝€欓€夋睜銆?- 鍙彁渚涙帓鐝簨瀹烇紝涓嶅喅瀹氬悗缁槸鍚︽帹鑽愭垨棰勭害銆?
鏄惁闇€瑕?LLM锛?
- 姝ｅ父涓嶉渶瑕?LLM銆?- 鏃堕棿鏍囧噯鍖栧拰妲戒綅鐞嗚В搴旂敱涓婃父 Understanding 灞傚畬鎴愩€?
杈撳嚭锛?
```python
availability_result.v1 = {
    "agent_name": "availability",
    "status": "completed | waiting_user | failed",
    "result_type": "availability_result",
    "facts": {
        "criteria": {},
        "options": [],
        "available_technician_names": []
    },
    "requires_user_input": False
}
```

#### Recommendation Agent

鑱岃矗锛?
- 璐熻矗鎵€鏈夆€滄帹鑽愮被浠诲姟鈥濓紝鍖呮嫭锛?  - 鏈嶅姟椤圭洰鎺ㄨ崘锛氫緥濡傗€滆叞閰歌儗鐥涙帹鑽愪粈涔堥」鐩紵鈥?  - 鎶€甯堟帹鑽愶細渚嬪鈥滄槑澶╀笅鍗堜笁鐐规湁鎺ㄨ崘鎶€甯堝悧锛熲€?  - 鎺ㄨ崘鏇挎崲锛氫緥濡傗€滄崲涓€涓€濃€滆繕鏈夊埆鐨勫悧锛熲€?  - 鎺ㄨ崘閫夋嫨鎵挎帴锛氫緥濡傗€滃氨浠栧惂鈥濃€滈€夌帇寮哄惂鈥?
椤圭洰鎺ㄨ崘鍜岀煡璇嗘煡璇㈢殑鍖哄埆锛?
- 鈥滀綘浠湁鍝簺椤圭洰锛熲€濆睘浜?Knowledge Agent銆?- 鈥滄垜鑵伴吀鑳岀棝锛屾帹鑽愪粈涔堥」鐩紵鈥濆睘浜?Recommendation Agent銆?- Recommendation Agent 鍙互璋冪敤鎴栨秷璐?Knowledge Agent/RAG 鐨勬湇鍔￠」鐩簨瀹烇紝浣嗘帹鑽愭帓搴忓拰鐞嗙敱鐢?Recommendation Agent 璐熻矗銆?
鏄惁闇€瑕?LLM锛?
- 鏈嶅姟椤圭洰鎺ㄨ崘鍙互鐢ㄨ鍒?+ 鏈嶅姟鐭ヨ瘑搴?+ LLM 瑙ｉ噴鐞嗙敱銆?- 鎶€甯堟帹鑽愬簲浼樺厛浣跨敤鍙害鍊欓€夋睜銆佸亸濂借蹇嗗拰 ranking service銆?- LLM 鍙互鐢ㄤ簬瑙ｉ噴鎺ㄨ崘鐞嗙敱锛屼絾涓嶈兘缂栭€犱笉瀛樺湪鐨勯」鐩€佷环鏍笺€佹妧甯堟垨鎺掔彮銆?
杈撳嚭锛?
```python
recommendation_result.v1 = {
    "agent_name": "recommendation",
    "status": "completed | awaiting_selection | waiting_user | failed",
    "result_type": "service_recommended | technician_recommended | recommendation_exhausted",
    "facts": {
        "recommended_service": {},
        "recommended_technician": {},
        "alternatives": [],
        "reason": "...",
        "source_facts": {}
    },
    "requires_user_input": True,
    "next_expected_user_action": "accept_recommendation | choose_alternative | provide_time | provide_service"
}
```

#### Booking Agent

鑱岃矗锛?
- 绠＄悊棰勭害鑽夌銆?- 琛ラ綈棰勭害妲戒綅锛氶」鐩€佹椂闂淬€佹椂闀裤€佹妧甯堛€?- 鐢熸垚纭鍗曘€?- 鍦ㄧ敤鎴锋槑纭‘璁ゅ悗鎵ц Guard銆?- Guard 閫氳繃鍚庡垱寤洪绾︺€?
鏄惁闇€瑕?LLM锛?
- Booking 鍐欐搷浣滀笉闇€瑕?LLM锛屼篃涓嶅厑璁?LLM 鍐冲畾鏄惁鍒涘缓棰勭害銆?- 鍙娇鐢ㄧ‘瀹氭€ц鍒欏鐞嗏€滅‘璁も€濃€滃彇娑堚€濃€滀慨鏀光€濈瓑琛屼负銆?- 鑷劧璇█琛ㄨ揪浜ょ粰 Response Writer锛屼絾纭鍗曞叧閿瓧娈靛繀椤绘潵鑷?Booking contract銆?
杈撳嚭锛?
```python
booking_result.v1 = {
    "agent_name": "booking",
    "status": "waiting_user | completed | failed",
    "result_type": "booking_missing | booking_confirmation | booking_created | booking_failed",
    "facts": {
        "draft": {},
        "missing_fields": [],
        "confirmation_summary": {},
        "guard_result": {}
    },
    "requires_user_input": True
}
```

### 4.4 Response Writer 缁熶竴鍥炲灞?
鑱岃矗锛?
- 鎺ユ敹 `ExecutionPlan`銆乣turn_results`銆乣last_agent_result`銆乣shared_focus_context`銆?- 鏍规嵁璁″垝鐘舵€佺粍缁囨渶缁堝洖澶嶃€?- 缁熶竴澶氫釜瀛?Agent 鐨勮緭鍑猴紝閬垮厤澶氫釜鏈哄櫒浜洪噸澶嶈璇濄€?- 瀵?Booking 鍏抽敭浜嬪疄鍙仛琛ㄨ揪锛屼笉鏀瑰啓浜嬪疄銆?
寤鸿鏂板锛?
```text
agents/response_writer/
  writer.py
  prompt.py
  schema.py
```

涔熷彲浠ョ涓€闃舵缁х画鏀惧湪锛?
```text
agents/supervisor/response_node.py
agents/response_writer/composer.py
```

浣嗗懡鍚嶅拰鑱岃矗涓婂簲閫愭杩佺Щ涓虹嫭绔?Writer銆?
Writer 鍥炲绛栫暐锛?
- `completed`锛氭€荤粨宸插畬鎴愮粨鏋溿€?- `waiting_user`锛氭槑纭憡璇夌敤鎴蜂笅涓€姝ラ渶瑕佽ˉ鍏呮垨纭浠€涔堛€?- `blocked`锛氳鏄庨樆濉炲師鍥狅紝骞剁粰鍑哄彲缁х画鐨勮緭鍏ユ柟寮忋€?- `failed`锛氳鏄庡け璐ュ師鍥犲拰鎭㈠寤鸿銆?
---

## 5. 鏍稿績鏁版嵁缁撴瀯

### 5.1 ExecutionPlan

```python
ExecutionPlan = {
    "plan_id": "plan_xxx",
    "goal": "涓虹敤鎴锋帹鑽愭槑澶╀笅鍗堜笁鐐瑰彲绾︽妧甯堬紝骞跺湪鐢ㄦ埛鎺ュ彈鍚庤繘鍏ラ绾︾‘璁?,
    "status": "pending | running | waiting_user | completed | blocked | failed",
    "source": "rule | context | llm | supervisor_review",
    "created_at": "...",
    "updated_at": "...",
    "tasks": [],
    "current_task_id": None,
    "completed_task_ids": [],
    "waiting_task_id": None,
    "blocked_reason": None,
    "completion_reason": None,
    "requires_user_input": False,
    "next_expected_user_action": None
}
```

### 5.2 PlanTask

```python
PlanTask = {
    "task_id": "t1",
    "agent": "availability | knowledge | recommendation | booking",
    "action": "query_availability | answer_knowledge | recommend_service | recommend_technician | start_or_continue_booking | confirm_booking",
    "status": "pending | running | completed | waiting_user | blocked | failed | skipped",
    "depends_on": [],
    "required": True,
    "input": {},
    "result_ref": None,
    "error": None
}
```

### 5.3 AgentResult

```python
AgentResult = {
    "version": "xxx_result.v1",
    "agent_name": "...",
    "status": "completed | awaiting_selection | waiting_user | blocked | failed",
    "result_type": "...",
    "response_type": "...",
    "facts": {},
    "state_updates": {},
    "tool_results": {},
    "requires_user_input": False,
    "next_expected_user_action": None,
    "suggested_next_tasks": [],
    "error": None
}
```

閲嶈鍙樺寲锛?
- 鍚庣画浠诲姟寤鸿缁熶竴浣跨敤 `suggested_next_tasks`锛屽苟鐢?Supervisor 鍐欏叆璁″垝鎴栬褰曟嫆缁濆師鍥犮€?- 瀛?Agent 鍙互寤鸿涓嬩竴姝ワ紝浣嗕笉鑳藉喅瀹氫笅涓€姝ャ€?- 涓嬩竴姝ユ槸鍚︽墽琛岋紝鍙兘鐢?Supervisor 鏍规嵁璁″垝鍜岀粨鏋滃垽鏂€?
---

## 6. LLM 浣跨敤杈圭晫

### 6.1 鍙互浣跨敤 LLM 鐨勪綅缃?
- 鎰忓浘鐞嗚В灞傜殑 LLM 鍏滃簳銆?- Supervisor Planner锛氬鏉傘€佸鎰忓浘銆佸姝ラ浠诲姟鍙敤 LLM 鐢熸垚璁″垝銆?- Supervisor Plan Reviewer锛氭嬁鍒板瓙 Agent 缁撴灉鍚庯紝蹇呰鏃剁敤 LLM 鍒ゆ柇鏄惁闇€瑕佽ˉ鍏呬换鍔°€?- Knowledge Agent锛歊AG 鍚庣粍缁囩煡璇嗗洖绛斻€?- Recommendation Agent锛氳В閲婃帹鑽愮悊鐢便€佸鐞嗘煍鎬у亸濂姐€?- Response Writer锛氱粍缁囨渶缁堝洖澶嶈瑷€銆?
### 6.2 涓嶅簲璇ヤ娇鐢?LLM 鑷敱鍐崇瓥鐨勪綅缃?
- Booking 鏄惁鍒涘缓棰勭害銆?- Booking Guard 鏄惁閫氳繃銆?- 鏁版嵁搴撳啓鎿嶄綔鍙傛暟銆?- 鍙害鎶€甯堟槸鍚﹀瓨鍦ㄣ€?- 鏈嶅姟椤圭洰浠锋牸銆佹椂闀裤€佸湴鍧€銆佽惀涓氭椂闂寸瓑浜嬪疄銆?
### 6.3 Supervisor 鐨?LLM 绛栫暐

Supervisor 鍙互璋冪敤 LLM 涓ゆ锛屼絾瑕佹湁杈圭晫锛?
1. **璁″垝鐢熸垚闃舵**锛氭牴鎹?TaskFrame 鍜岀姸鎬佺敓鎴?ExecutionPlan銆?2. **缁撴灉妫€鏌ラ樁娈?*锛氬綋瑙勫垯鏃犳硶鏄庣‘鍒ゆ柇鏄惁瀹屾垚鏃讹紝杈呭姪鍒ゆ柇鏄惁闇€瑕佺户缁皟鐢ㄥ叾浠?Agent銆?
浼樺厛绾у缓璁細

```text
纭畾鎬ц鍒欐鏌?> 璁″垝鐘舵€佹鏌?> LLM Plan Reviewer > fallback/clarification
```

杩欐牱鏃㈣兘浣撶幇澶氭櫤鑳戒綋鏅鸿兘缂栨帓锛屽張涓嶄細璁?LLM 鎺ョ鍏抽敭涓氬姟瀹夊叏杈圭晫銆?
---

## 7. 鍏稿瀷浠诲姟璁″垝鏄犲皠

### 7.1 闈欐€佸挩璇?
```text
鐢ㄦ埛锛氫綘浠湁鍝簺椤圭洰锛?Plan:
  1. knowledge.answer_service_catalog
  2. writer.final_answer
```

### 7.2 椤圭洰鎺ㄨ崘

```text
鐢ㄦ埛锛氭垜鑵伴吀鑳岀棝锛屾帹鑽愪粈涔堥」鐩紵
Plan:
  1. recommendation.recommend_service
  2. writer.final_answer
```

璇存槑锛?
- Recommendation Agent 鍙鍙栨湇鍔＄煡璇嗗簱銆?- 鎺ㄨ崘缁撴灉搴斿啓鍏?`shared_focus_context.service_type`锛屾柟渚垮悗缁绾︽垨鎶€甯堟帹鑽愭壙鎺ャ€?
### 7.3 鏌ヨ鎺掔彮

```text
鐢ㄦ埛锛氭槑澶╀笅鍗堜笁鐐规湁鍝簺鎶€甯堬紵
Plan:
  1. availability.query_availability
  2. writer.final_answer
```

### 7.4 鎶€甯堟帹鑽?
```text
鐢ㄦ埛锛氭槑澶╀笅鍗堜笁鐐规湁鎺ㄨ崘鐨勬妧甯堝悧锛?Plan:
  1. availability.query_availability
  2. recommendation.recommend_technician
  3. writer.final_answer
```

### 7.5 鏌ヨ鍚庣户缁帹鑽?
```text
鐢ㄦ埛锛氭槑澶╀笅鍗堜笁鐐规湁鍝簺鎶€甯堬紵浣犳帹鑽愯皝锛?Plan:
  1. availability.query_availability
  2. recommendation.recommend_technician
  3. writer.final_answer
```

### 7.6 鎺ㄨ崘鍚庤繘鍏ラ绾?
```text
鐢ㄦ埛锛氬氨浠栧惂
Plan:
  1. booking.select_recommended_technician
  2. booking.start_or_continue_booking
  3. writer.final_answer
```

濡傛灉椤圭洰銆佹椂闂淬€佹椂闀裤€佹妧甯堝凡瀹屾暣锛?
```text
Booking 杈撳嚭 booking_confirmation锛岀瓑寰呯敤鎴风‘璁?```

濡傛灉浠嶇己妲戒綅锛?
```text
Booking 杈撳嚭 booking_missing锛岀瓑寰呯敤鎴疯ˉ鍏?```

### 7.7 纭棰勭害

```text
鐢ㄦ埛锛氱‘璁ら绾?Plan:
  1. booking.confirm_booking
  2. writer.final_answer
```

Booking 鍐呴儴蹇呴』瀹屾垚锛?
```text
鐢ㄦ埛纭 -> Guard -> 鏁版嵁搴撳垱寤?-> booking_created
```

---

## 8. 鏀归€犻樁娈?
### 闃舵闆讹細鍩虹嚎姊崇悊涓庡洖褰掍繚鎶?
鐩爣锛?
- 鍦ㄦ寮忔敼閫犲墠鍐荤粨褰撳墠琛屼负鍩虹嚎锛岄伩鍏嶅悗缁噸鏋勬椂涓嶇煡閬撳摢閲岃鏀瑰潖銆?- 鍏堟妸鈥滃綋鍓嶈兘鍋氫粈涔堛€佸摢閲屾湁闂銆佸摢浜涢摼璺繀椤讳繚鎸佲€濊褰曟竻妤氥€?
娑夊強鑼冨洿锛?
```text
README.md
ARCHITECTURE_3_0.md
MATURE_AGENT_LAYER_FRAMEWORK.md
tests/
```

宸ヤ綔鍐呭锛?
- 姊崇悊褰撳墠涓婚摼璺細`understanding -> supervisor_router -> specialist -> response_node`銆?- 鏁寸悊褰撳墠鐘舵€佸瓧娈碉細`task_frame`銆乣route_decision`銆乣shared_focus_context`銆乣turn_results`銆乣last_agent_result`銆乣consultation`銆乣availability`銆乣recommendation`銆乣booking`銆?- 鍥哄寲鏍稿績鍥炲綊鐢ㄤ緥锛?  - 闈欐€佸挩璇細椤圭洰銆佷环鏍笺€佸湴鍧€銆佽惀涓氭椂闂淬€?  - 椤圭洰鎺ㄨ崘锛氳叞閰歌儗鐥涙帹鑽愰」鐩€?  - 鎺掔彮鏌ヨ锛氭煇鏃堕棿鏈夊摢浜涙妧甯堛€?  - 鎶€甯堟帹鑽愶細鏌愭椂闂存帹鑽愭妧甯堛€?  - 鎺ㄨ崘鎵挎帴棰勭害锛氭帹鑽愰」鐩?-> 鎺ㄨ崘鎶€甯?-> 閫夋嫨鎶€甯?-> 鐢熸垚纭鍗曘€?  - Booking Guard锛氭湭纭涓嶅垱寤恒€佺己妲戒綅涓嶅垱寤恒€佷笉鍙害涓嶅垱寤恒€?- 缁欐瘡涓敤渚嬭褰曟湡鏈涚姸鎬佸彉鍖栧拰鏈€缁堝洖澶嶃€?
鐘舵€佷笌涓婁笅鏂囪姹傦細

- 涓嶆敼瀛楁锛屽彧璁板綍瀛楁鏉ユ簮銆佺敤閫斿拰褰撳墠闂銆?- 鏄庣‘鍝簺瀛楁鍚庣画浼氫繚鐣欍€佸吋瀹广€佽縼绉绘垨搴熷純銆?
宸ュ叿璋冪敤瑕佹眰锛?
- 璁板綍褰撳墠宸ュ叿/鏈嶅姟璋冪敤鐐癸細鐭ヨ瘑妫€绱€佹帓鐝煡璇€佹妧甯堟帓搴忋€侀绾﹀垱寤恒€?- 鏍囨敞鍝簺鏄宸ュ叿锛屽摢浜涙槸鍐欏伐鍏凤紝鍝簺蹇呴』骞傜瓑銆?
Prompt 瑕佹眰锛?
- 璁板綍褰撳墠 LLM 鍙備笌鐐癸細鎰忓浘鍏滃簳銆佺煡璇嗗洖绛斻€佹帹鑽愮悊鐢便€佸洖澶嶇粍缁囩瓑銆?- 鏍囨敞姣忎釜 prompt 鐨勮緭鍏ャ€佽緭鍑恒€佸け璐ュ厹搴曠瓥鐣ャ€?
楠屾敹鏍囧噯锛?
- 鏈変竴缁勫彲杩愯鐨勫洖褰掓祴璇曟垨鎵嬪伐楠岃瘉娓呭崟銆?- 鏄庣‘褰撳墠鐘舵€佸瓧娈靛湴鍥俱€?- 鍚庣画浠讳綍闃舵閮借兘鐢ㄨ鍩虹嚎鍒ゆ柇鏄惁琛屼负鍥為€€銆?
---

### 闃舵涓€锛氱姸鎬佷笌涓婁笅鏂囧绾﹂噸鏋?
鐩爣锛?
- 鍏堟妸鐘舵€佽竟鐣岀悊娓呮锛屽啀鍋氬 Agent 缂栨帓銆?- 鏄庣‘鈥滅敤鎴锋鍦ㄨ皥浠€涔堚€濆拰鈥滅郴缁熸墽琛屽埌鍝竴姝モ€濆垎鍒斁鍦ㄥ摢閲屻€?
鏂板/淇敼鏂囦欢锛?
```text
agents/supervisor/state.py
agents/shared/context_schema.py          # 鏂板锛氬叡浜笂涓嬫枃 schema
agents/shared/context_manager.py         # 鏂板锛氫笂涓嬫枃璇诲啓銆佸悎骞躲€佸け鏁堣鍒?services/session_state_store.py
api/graph_state_view.py
```

鐘舵€佸垎灞傦細

```text
task_frame
  鏈疆鐢ㄦ埛璇箟锛氭剰鍥俱€佹Ы浣嶃€佺己澶变俊鎭€佹潵婧愩€佺疆淇″害銆?
shared_focus_context
  璺?Agent 褰撳墠鐒︾偣锛氭湇鍔￠」鐩€佹椂闂淬€佹椂闀裤€佹妧甯堛€佸亸濂姐€佺棁鐘躲€佷笂涓€杞帹鑽愩€?
execution_plan
  Supervisor 鎵ц鐘舵€侊細璁″垝銆佸綋鍓嶄换鍔°€佸凡瀹屾垚浠诲姟銆佺瓑寰呯敤鎴峰姩浣溿€佸畬鎴愬師鍥犮€?
turn_results
  鏈疆鎵€鏈夊瓙 Agent 鐨勭粨鏋勫寲缁撴灉銆?
agent_private_state
  鍚勯鍩熷唴閮ㄧ姸鎬侊細consultation/knowledge銆乤vailability銆乺ecommendation銆乥ooking銆?```

`shared_focus_context` 寤鸿鎵╁睍锛?
```python
shared_focus_context = {
    "service_type": None,
    "start_time": None,
    "duration_minutes": None,
    "technician_name": None,
    "technician_id": None,
    "gender_preference": None,
    "preference": None,
    "symptom_or_need": None,
    "recommended_service": None,
    "selected_recommendation_ref": None,
    "last_offer": None,
    "context_source": {},
    "updated_by": None,
    "updated_at": None,
}
```

鏉ユ簮浼樺厛绾э細

```text
鐢ㄦ埛鏈疆鏄庣‘杈撳叆 > 鐢ㄦ埛鏈疆纭/閫夋嫨 > Booking draft > Recommendation selected > Availability criteria > 鍘嗗彶涓婁笅鏂?```

涓婁笅鏂囧け鏁堣鍒欙細

- 鐢ㄦ埛淇敼鏃堕棿锛屽垯娓呯┖渚濊禆鏃ф椂闂寸殑 `availability.options` 鍜屾妧甯堟帹鑽愩€?- 鐢ㄦ埛淇敼鏈嶅姟椤圭洰锛屽垯娓呯┖渚濊禆鏃ч」鐩殑鎶€甯堟帹鑽愬拰棰勭害纭鍗曘€?- 鐢ㄦ埛淇敼鎶€甯堬紝鍒欐竻绌烘棫鎺ㄨ崘閫夋嫨鍜屾棫纭鍗曘€?- 鐢ㄦ埛纭 Booking 鍚庯紝淇濈暀 `last_completed_booking`锛岄噸缃?active booking draft銆?
瀛楁杩佺Щ绛栫暐锛?
```text
route_decision
  鐭湡淇濈暀锛岀敤浣滃吋瀹瑰拰 trace锛涢暱鏈熶笉浣滀负涓绘墽琛岄┍鍔ㄣ€?
task_stack
  杩佺Щ鍒?execution_plan.tasks銆?
suggested_next_tasks
  瀛?Agent 瀵瑰悗缁换鍔＄殑鍞竴寤鸿瀛楁锛汼upervisor 鏍￠獙鍚庢墠鍙拷鍔犲埌 execution_plan銆?
last_agent_result
  鐭湡淇濈暀锛涢暱鏈熶綔涓?turn_results[-1] 鐨勫揩鎹峰紩鐢ㄣ€?```

楠屾敹鏍囧噯锛?
- 鐘舵€佸垵濮嬪寲銆佹寔涔呭寲銆丄PI 鐘舵€佽鍥鹃兘鏀寔鏂板瓧娈点€?- 浠讳綍涓€涓法 Agent 鎵挎帴閾捐矾閮借兘浠?`shared_focus_context` 鎵惧埌涓讳笂涓嬫枃銆?- 淇敼鏃堕棿/椤圭洰/鎶€甯堟椂锛岀浉鍏充笅娓哥姸鎬佷細琚竻鐞嗭紝涓嶄細浣跨敤杩囨湡鍊欓€夋睜鎴栫‘璁ゅ崟銆?
---

### 闃舵浜岋細鎰忓浘鐞嗚В杈撳嚭瀵归綈澶?Agent 璁″垝

鐩爣锛?
- 璁╂剰鍥剧悊瑙ｅ眰杈撳嚭瓒冲绋冲畾鐨勪换鍔¤涔夛紝渚?Supervisor 鐢熸垚璁″垝銆?- 淇濇寔鈥滆鍒欏眰 + 涓婁笅鏂囧寮?+ LLM 鍏滃簳鈥濈殑涓夊眰缁撴瀯锛屼絾杈撳嚭瑕佸榻愬 Agent 鏋舵瀯銆?
淇敼鏂囦欢锛?
```text
agents/understander/schemas.py
agents/understander/rules.py
agents/understander/contextual_resolver.py
agents/understander/llm_planner.py
agents/understander/decision_builder.py
agents/understander/decision_arbiter.py
```

浠诲姟绫诲瀷琛ラ綈锛?
```text
knowledge_consultation
availability_query
service_recommendation
technician_recommendation
recommendation_replacement
recommendation_selection
booking_creation
booking_modification
booking_confirmation
booking_cancel
clarification
unsupported
multi_intent
context_operation
```

杈撳嚭瑕佹眰锛?
```python
TaskFrame = {
    "task_type": "...",
    "primary_intent": "...",
    "secondary_intents": [],
    "slots": {},
    "missing_slots": [],
    "context_links": [],
    "confidence": 0.0,
    "source": "rule | context | llm",
    "needs_planning": True,
    "query_first": False,
    "safety_flags": [],
}
```

宸ヤ綔鍐呭锛?
- 瑙勫垯灞傛槑纭尯鍒嗭細
  - 鈥滄湁鍝簺椤圭洰/浠锋牸/鍦板潃鈥?-> `knowledge_consultation`
  - 鈥滄帹鑽愪粈涔堥」鐩?鎴戝摢閲屼笉鑸掓湇閫傚悎浠€涔堚€?-> `service_recommendation`
  - 鈥滄煇鏃堕棿鏈夊摢浜涗汉鈥?-> `availability_query`
  - 鈥滄帹鑽愭妧甯?鎹竴涓?灏变粬鍚р€?-> `technician_recommendation` 鎴栨帹鑽愭壙鎺ョ被浠诲姟
  - 鈥滃府鎴戠害/纭/鍙栨秷/鏀规椂闂粹€?-> Booking 绫讳换鍔?- 涓婁笅鏂囧寮哄眰璐熻矗琛ュ叏鎸囦唬鍜岀渷鐣ワ細
  - 鈥滃氨浠栧惂鈥濈粦瀹氫笂涓€杞帹鑽愭妧甯堛€?  - 鈥滄垜鎯虫槑澶╀笅鍗堜笁鐐瑰幓鈥濊ˉ鍏ㄤ笂涓€杞帹鑽愰」鐩€?  - 鈥滄崲涓€涓€濈粦瀹氫笂涓€杞帹鑽愭睜銆?- LLM 鍏滃簳杈撳嚭蹇呴』鍜岃鍒欏眰涓€鑷达紝涓嶈兘杩斿洖鑷敱鏍煎紡銆?- `decision_builder` 涓嶅啀鎵挎媴澶嶆潅鎵ц椤哄簭锛屽彧鎻忚堪浠诲姟璇箟鍜屽繀瑕?continuation hint銆?
Prompt 瑕佹眰锛?
- `llm_planner.py` 鐨?prompt 搴旀敼鍚嶆垨瀹氫綅涓?understanding fallback prompt锛岄伩鍏嶅拰 Supervisor Planner 娣锋穯銆?- LLM 鍏滃簳 prompt 蹇呴』杈撳嚭鍙楅檺 JSON锛歚task_type`銆乣intents`銆乣slots`銆乣confidence`銆乣reason`銆?- LLM 涓嶅厑璁歌緭鍑虹洿鎺ュ伐鍏疯皟鐢ㄦ垨棰勭害鍐欐搷浣溿€?
楠屾敹鏍囧噯锛?
- 甯歌纭畾鎬ц〃杈句紭鍏堣瑙勫垯鍛戒腑銆?- 鎸囦唬銆佺渷鐣ャ€佹帹鑽愭壙鎺ヨ兘鐢变笂涓嬫枃澧炲己琛ラ綈銆?- LLM 鍏滃簳缁撴灉鑳借 schema 鏍￠獙锛屽け璐ユ椂杩涘叆 clarification/unsupported銆?- `TaskFrame` 瓒充互璁?Supervisor 鐢熸垚璁″垝銆?
---

### 闃舵涓夛細寮曞叆 ExecutionPlan 涓庣‘瀹氭€?Planner

鐩爣锛?
- 鍦ㄧ姸鎬佷腑鍔犲叆鏄惧紡璁″垝瀵硅薄銆?- 鍏堢敤纭畾鎬?Planner 浠?`TaskFrame` 鐢熸垚 `ExecutionPlan`锛屼笉绔嬪嵆寮曞叆澶嶆潅 LLM 缂栨帓銆?
鏂板鏂囦欢锛?
```text
agents/supervisor/plan_schema.py
agents/supervisor/plan_state.py
agents/supervisor/planner.py
```

淇敼鏂囦欢锛?
```text
agents/supervisor/state.py
agents/supervisor/nodes.py
services/session_state_store.py
api/graph_state_view.py
```

鏍稿績缁撴瀯锛?
```python
ExecutionPlan = {
    "plan_id": "...",
    "goal": "...",
    "status": "pending | running | waiting_user | completed | blocked | failed",
    "source": "rule | context | llm | supervisor",
    "tasks": [],
    "current_task_id": None,
    "completed_task_ids": [],
    "waiting_task_id": None,
    "requires_user_input": False,
    "next_expected_user_action": None,
    "completion_reason": None,
}
```

Planner 杈撳叆锛?
```text
TaskFrame
RouteDecision
shared_focus_context
availability / recommendation / booking state
```

纭畾鎬ф槧灏勶細

```text
knowledge_consultation
  -> [knowledge.answer_knowledge]

availability_query
  -> [availability.query_availability]

service_recommendation
  -> [recommendation.recommend_service]

technician_recommendation
  -> [availability.query_availability, recommendation.recommend_technician]

recommendation_selection
  -> [booking.select_recommended_technician, booking.start_or_continue_booking]

booking_creation
  -> [booking.start_or_continue_booking]

booking_modification
  -> [booking.modify_booking]

booking_confirmation
  -> [booking.confirm_booking]

multi_intent(query_first=True)
  -> [knowledge/availability first, then recommendation/booking]
```

鐘舵€佽姹傦細

- `execution_plan` 姣忚疆閲嶆柊鐢熸垚鎴栧熀浜庡緟纭浠诲姟鎭㈠銆?- 绛夊緟鐢ㄦ埛鐨勮鍒掗渶瑕佷繚鐣?`waiting_task_id` 鍜?`next_expected_user_action`銆?- 鏂扮敤鎴疯緭鍏ュ埌鏉ユ椂锛屽厛鐢?understanding 鍒ゆ柇鏄€滅户缁棫璁″垝鈥濊繕鏄€滄柊浠诲姟瑕嗙洊鏃ц鍒掆€濄€?
宸ュ叿璋冪敤瑕佹眰锛?
- Planner 涓嶈皟鐢ㄤ笟鍔″伐鍏枫€?- Planner 鍙敓鎴愬彈闄?`PlanTask`銆?
Prompt 瑕佹眰锛?
- 鏈樁娈典笉寮曞叆 LLM Planner銆?- 鍏堢敤纭畾鎬ф槧灏勮绯荤粺琛屼负鍙В閲娿€?
楠屾敹鏍囧噯锛?
- 姣忚疆閮芥湁 `execution_plan`銆?- `route_decision` 浠嶄繚鐣欏吋瀹癸紝浣嗚鍒掓槸涓昏 trace 瀵硅薄銆?- 椤圭洰鎺ㄨ崘鐢熸垚 `recommendation.recommend_service`銆?- 鎶€甯堟帹鑽愮敓鎴?`availability.query_availability -> recommendation.recommend_technician`銆?- 鎺ㄨ崘閫夋嫨鐢熸垚 `booking.select_recommended_technician -> booking.start_or_continue_booking`銆?
---

### 闃舵鍥涳細宸ュ叿璋冪敤灞備笌宸ュ叿濂戠害鏁寸悊

鐩爣锛?
- 鍦ㄥ瓙 Agent 鐪熸鎸夎鍒掓墽琛屽墠锛屽厛缁熶竴宸ュ叿璋冪敤杈圭晫銆?- 鏄庣‘鍝簺宸ュ叿鍙銆佸摢浜涘伐鍏峰彲鍐欍€佸摢浜涘伐鍏峰繀椤荤粡杩?Guard銆?
鏂板/淇敼鏂囦欢锛?
```text
tools/
services/
agents/specialists/*/actions.py
agents/specialists/*/tool_contract.py
```

宸ュ叿鍒嗙被锛?
```text
Knowledge tools
  - search_knowledge
  - get_service_catalog
  - get_store_info

Availability tools
  - query_schedule
  - filter_available_technicians

Recommendation tools
  - rank_services
  - rank_technicians
  - recall_preferences

Booking tools
  - validate_booking_guard
  - create_booking
  - cancel_booking
  - update_booking
```

濂戠害瑕佹眰锛?
```python
ToolResult = {
    "tool_name": "...",
    "status": "success | failed",
    "data": {},
    "error": None,
    "trace": {},
}
```

宸ュ叿瀹夊叏杈圭晫锛?
- 璇诲伐鍏峰彲浠ョ敱瀵瑰簲瀛?Agent 鐩存帴璋冪敤銆?- 鍐欏伐鍏峰彧鑳界敱 Booking Agent 璋冪敤銆?- `create_booking` 蹇呴』婊¤冻锛氱敤鎴风‘璁?+ 妲戒綅瀹屾暣 + Guard 閫氳繃 + 骞傜瓑閿瓨鍦ㄣ€?- 浠讳綍 LLM 杈撳嚭閮戒笉鑳界洿鎺ヤ綔涓哄啓宸ュ叿鍙傛暟锛屽繀椤荤粡杩囩粨鏋勫寲鐘舵€佸拰 Guard銆?
鐘舵€佷笌涓婁笅鏂囪姹傦細

- 宸ュ叿缁撴灉鍐欏叆瀵瑰簲 Agent 绉佹湁鐘舵€佸拰 `turn_results.facts`銆?- 鍏抽敭宸ュ叿缁撴灉鎽樿鍐欏叆 `tool_results`锛岀敤浜?trace銆?- 涓嶆妸澶ф鍘熷鏂囨。鎴栧叏閲忔暟鎹簱缁撴灉濉炶繘鍏ㄥ眬鐘舵€侊紝鍙繚瀛樺繀瑕佹憳瑕佸拰寮曠敤銆?
楠屾敹鏍囧噯锛?
- 姣忎釜瀛?Agent 鐨勫伐鍏疯緭鍏?杈撳嚭鏍煎紡鍥哄畾銆?- Booking 鍐欏伐鍏峰叿澶囩‘璁ゃ€丟uard 鍜屽箓绛変繚鎶ゃ€?- Supervisor 涓嶇洿鎺ヨ皟鐢ㄤ换浣曚笟鍔″伐鍏枫€?
---

### 闃舵浜旓細Controller 鎸夎鍒掕皟鐢ㄥ瓙 Agent

鐩爣锛?
- Supervisor 浠?route-first 杩佺Щ鍒?plan-first銆?- Controller 鏍规嵁 `ExecutionPlan.current_task` 璋冪敤瀛?Agent锛岃€屼笉鏄洿鎺ユ牴鎹?`route_decision.action` 璺敱銆?
鏂板鏂囦欢锛?
```text
agents/supervisor/controller.py
```

淇敼鏂囦欢锛?
```text
agents/supervisor/graph_builder.py
agents/supervisor/nodes.py
agents/supervisor/routing.py
```

宸ヤ綔鍐呭锛?
- 鎵惧埌涓嬩竴涓彲鎵ц `PlanTask`銆?- 灏?`PlanTask` 閫傞厤鍒板綋鍓嶅瓙鍥捐妭鐐广€?- 鎵ц鍓嶆妸 `PlanTask.status` 鏍囪涓?`running`銆?- 瀛?Agent 杩斿洖鍚庯紝鎶?`AgentResult` 鍐欏叆 `turn_results`銆?- 灏?`PlanTask.result_ref` 鎸囧悜瀵瑰簲 `turn_results` 涓嬫爣鎴?result id銆?- 鏍规嵁瀛?Agent 鐘舵€佹洿鏂?`PlanTask.status`銆?
鍏煎璺緞锛?
```text
鐭湡锛歍askFrame -> RouteDecision -> ExecutionPlan -> route adapter
闀挎湡锛歍askFrame -> ExecutionPlan -> Controller -> Child Agent
```

鐘舵€佽姹傦細

- `current_task_id` 蹇呴』鍜屾鍦ㄦ墽琛岀殑瀛?Agent 瀵归綈銆?- `completed_task_ids` 鍙褰曠湡姝ｅ畬鎴愮殑浠诲姟銆?- `waiting_task_id` 璁板綍闇€瑕佺敤鎴疯ˉ鍏呮垨纭鐨勪换鍔°€?
宸ュ叿璋冪敤瑕佹眰锛?
- Controller 涓嶇洿鎺ヨ皟鐢ㄥ伐鍏凤紝鍙皟鐢ㄥ瓙 Agent銆?- 瀛?Agent 鐨勫伐鍏疯皟鐢ㄧ粨鏋滈€氳繃 `AgentResult.tool_results` 杩斿洖銆?
楠屾敹鏍囧噯锛?
- 鍗曟浠诲姟琛屼负涓嶅彉銆?- 澶氭浠诲姟鑳界敱璁″垝鑷姩鎺ㄨ繘銆?- `execution_plan.tasks[].result_ref` 鑳藉搴斿埌 `turn_results`銆?- 褰撳墠 query-first continuation 鐢?`ExecutionPlan` 灞曞紑涓哄姝ヤ换鍔★紱鏃?route-level 缁帴鍏滃簳宸茬Щ闄ゃ€?
---

### 闃舵鍏細缁熶竴瀛?Agent 缁撴灉濂戠害

鐩爣锛?
- 鎵€鏈夊瓙 Agent 閮戒互绋冲畾缁撴瀯杩斿洖缁撴灉锛孲upervisor 鍜?Writer 涓嶅啀鐚滄祴鍐呴儴鐘舵€併€?
鏂板/淇敼鏂囦欢锛?
```text
agents/specialists/result_contract.py
agents/specialists/availability/result_contract.py
agents/specialists/recommendation/result_contract.py
agents/specialists/consultation/result_contract.py
agents/specialists/booking/result_contract.py
```

缁熶竴缁撴瀯锛?
```python
AgentResult = {
    "version": "xxx_result.v1",
    "agent_name": "...",
    "status": "completed | waiting_user | awaiting_selection | blocked | failed",
    "result_type": "...",
    "response_type": "...",
    "facts": {},
    "state_updates": {},
    "tool_results": {},
    "requires_user_input": False,
    "next_expected_user_action": None,
    "suggested_next_tasks": [],
    "error": None,
}
```

姣忎釜 Agent 鐨勭粨鏋滐細

```text
knowledge_result.v1
availability_result.v1
recommendation_result.v1
booking_result.v1
fallback_result.v1
```

鐘舵€佷笌涓婁笅鏂囪姹傦細

- `facts` 鏀?Writer 闇€瑕佽〃杈剧殑浜嬪疄銆?- `state_updates` 鏀鹃渶瑕佸悎骞跺洖鍏ㄥ眬鐘舵€佺殑棰嗗煙鐘舵€併€?- `suggested_next_tasks` 鍙綔涓哄缓璁紝涓嶇洿鎺ヨ矾鐢便€?- `requires_user_input` 鍜?`next_expected_user_action` 蹇呴』鏄惧紡銆?
楠屾敹鏍囧噯锛?
- Supervisor 涓嶅啀閫氳繃鑷劧璇█ message 鍒ゆ柇瀛?Agent 鏄惁鎴愬姛銆?- Response Writer 鍙秷璐规爣鍑?result contract銆?- 姣忎釜 AgentResult 閮藉彲琚祴璇曟柇瑷€銆?
---

### 闃舵涓冿細Completion Checker 涓庤鍒掍慨姝?
鐩爣锛?
- Supervisor 鍦ㄦ瘡涓瓙 Agent 杩斿洖鍚庡垽鏂笅涓€姝ャ€?- 瀛?Agent 鍙彁渚涚粨鏋滃拰寤鸿锛屼笉鍐冲畾涓嬩竴姝ャ€?
鏂板鏂囦欢锛?
```text
agents/supervisor/completion.py
agents/supervisor/plan_reviewer.py      # 鍙€夛紝鍚庣画寮曞叆 LLM Reviewer
```

宸ヤ綔鍐呭锛?
- 鏍规嵁 `AgentResult.status` 鏇存柊 `ExecutionPlan.status`銆?- 鏍规嵁 `requires_user_input` 鍐冲畾鏄惁缁撴潫鏈疆骞剁瓑寰呯敤鎴枫€?- 鏍规嵁鍓╀綑 `PlanTask` 鍐冲畾鏄惁缁х画鎵ц銆?- 鏍规嵁 `suggested_next_tasks` 鍐冲畾鏄惁杩藉姞璁″垝銆?- 瀵瑰嵄闄╀换鍔″仛鎷掔粷锛屼緥濡傛湭纭鏃朵笉鑳借拷鍔?`booking.confirm_booking`銆?
纭畾鎬ц鍒欙細

```text
current task completed + has runnable next task -> continue
current task waiting_user / awaiting_selection -> response, wait user
current task blocked -> clarification or fallback
all required tasks completed -> response
required task failed -> failure response or recovery task
booking confirmation -> wait user
booking created -> completed
```

LLM Reviewer 浣跨敤杈圭晫锛?
- 鍙湁鍦ㄧ‘瀹氭€ц鍒欐棤娉曞垽鏂€滄槸鍚﹀凡婊¤冻鐢ㄦ埛鐩爣鈥濇椂鍚敤銆?- 杈撳叆涓鸿鍒掓憳瑕佸拰缁撴瀯鍖?AgentResult锛屼笉杈撳叆鍏ㄩ噺绉佹湁鐘舵€併€?- 杈撳嚭鍙厑璁革細`continue`銆乣wait_user`銆乣complete`銆乣blocked`銆乣append_allowed_task`銆?- 涓嶅厑璁歌緭鍑虹洿鎺ュ伐鍏疯皟鐢ㄣ€?
Prompt 瑕佹眰锛?
- 鏂板 reviewer prompt锛屽繀椤诲寘鍚厑璁哥殑 agent/action 鐧藉悕鍗曘€?- reviewer 杈撳嚭蹇呴』 schema 鏍￠獙锛屽け璐ュ垯璧扮‘瀹氭€т繚瀹堢瓥鐣ャ€?
楠屾敹鏍囧噯锛?
- Recommendation 瀹屾垚鍚庨粯璁ょ瓑寰呯敤鎴烽€夋嫨锛屼笉鑷姩鍒涘缓棰勭害銆?- Booking confirmation 鍚庣瓑寰呯敤鎴风‘璁わ紝涓嶈嚜鍔ㄥ垱寤洪绾︺€?- query-first 澶氫换鍔″彲浠ヨ嚜鍔ㄧ户缁墽琛屻€?- 瀛?Agent 鐨勪笅涓€姝ュ缓璁笉浼氱粫杩?Supervisor銆?
---

### 闃舵鍏細寤鸿浠诲姟娌荤悊锛岀粺涓€涓?suggested_next_tasks

鐩爣锛?
- 浠庘€滃瓙 Agent 鏀?route鈥濊縼绉讳负鈥滃瓙 Agent 缁欏缓璁紝Supervisor 璇勪及鍚庢敼 plan鈥濄€?
褰撳墠浠ｇ爜锛?
```text
agents/supervisor/agent_registry.py
agents/supervisor/nodes.py
agents/supervisor/routing.py
agents/specialists/result_contract.py
```

鏀归€犳柟鍚戯細

- 鍙繚鐣?`suggested_next_tasks`銆?- `agent_registry.py` 鍙繚瀛?action 鍒?Agent 鐨勫厑璁告槧灏勩€?- `controller.py` 璐熻矗鏍￠獙銆佽拷鍔犳垨鎷掔粷寤鸿浠诲姟銆?- Supervisor 鍙湪璁″垝鏍￠獙閫氳繃鍚庤拷鍔犱换鍔°€?- 鎵€鏈夊缓璁拰閲囩撼/鎷掔粷鍘熷洜杩涘叆 trace銆?
鐘舵€佽姹傦細

- `execution_plan.tasks` 鏄敮涓€浠诲姟闃熷垪銆?- 寤鸿浠诲姟杈撳叆鍐欏叆 `PlanTask.input` 鎴?`AgentResult.facts`銆?- `route_decision` 涓嶄繚瀛樺瓙 Agent 鐢熸垚鐨勪笅涓€姝ヤ富鍐崇瓥銆?
楠屾敹鏍囧噯锛?
- Availability 鍙互寤鸿 Recommendation锛屼絾鏄惁鎵ц鐢?Supervisor 鍐冲畾銆?- Recommendation 鍙互寤鸿 Booking selection锛屼絾蹇呴』绛夊緟鐢ㄦ埛鎺ュ彈銆?- Booking 鍐欐搷浣滀笉鑳介€氳繃 suggested task 缁曡繃纭銆?
---

### 闃舵涔濓細Recommendation Agent 鎵╁睍涓虹粺涓€鎺ㄨ崘 Agent

鐩爣锛?
- 鎺ㄨ崘 Agent 鍚屾椂鏀寔椤圭洰鎺ㄨ崘鍜屾妧甯堟帹鑽愩€?
鏂板/淇敼锛?
```text
agents/specialists/recommendation/actions.py
agents/specialists/recommendation/nodes.py
agents/specialists/recommendation/result_contract.py
services/service_recommendation_service.py
services/technician_recommendation_service.py
```

鑳藉姏鎷嗗垎锛?
```text
recommend_service
  杈撳叆锛氱棁鐘?鍋忓ソ/棰勭畻/鏃堕暱/鍘嗗彶涓婁笅鏂?  宸ュ叿锛氭湇鍔＄洰褰曘€佺煡璇嗗簱/RAG銆佽鍒欏尮閰?  杈撳嚭锛氭帹鑽愰」鐩€佸閫夐」鐩€佺悊鐢?
recommend_technician
  杈撳叆锛氭椂闂淬€侀」鐩€佹椂闀裤€佸亸濂姐€佸彲绾﹀€欓€夋睜
  宸ュ叿锛氭帓鐝粨鏋溿€佹妧甯堢敾鍍忋€佸亸濂借蹇嗐€乺anking service
  杈撳嚭锛氭帹鑽愭妧甯堛€佸閫夋妧甯堛€佺悊鐢?
replace_recommendation
  杈撳叆锛氬綋鍓嶆帹鑽愩€佹帓闄ゅ垪琛ㄣ€佸亸濂藉彉鍖?  杈撳嚭锛氭柊鐨勬帹鑽?```

鐘舵€佷笌涓婁笅鏂囪姹傦細

- 椤圭洰鎺ㄨ崘缁撴灉鍐欏叆锛?  - `recommendation.selected_service_recommendation`
  - `shared_focus_context.service_type`
  - `shared_focus_context.recommended_service`
- 鎶€甯堟帹鑽愮粨鏋滃啓鍏ワ細
  - `recommendation.selected_recommendation`
  - `shared_focus_context.technician_name`
  - `shared_focus_context.technician_id`
  - `shared_focus_context.selected_recommendation_ref`
- 鈥滄崲涓€涓€濊鏇存柊鎺掗櫎鍒楄〃锛屼笉姹℃煋 Booking draft銆?
宸ュ叿璋冪敤瑕佹眰锛?
- 椤圭洰鎺ㄨ崘鍙互璇诲彇鏈嶅姟鐩綍鍜岀煡璇嗗簱銆?- 鎶€甯堟帹鑽愬繀椤讳紭鍏堟秷璐?Availability 鐨勫€欓€夋睜銆?- 鏃犲€欓€夋睜鏃惰繑鍥?`waiting_user` 鎴?`suggested_next_tasks=[availability.query_availability]`銆?
Prompt 瑕佹眰锛?
- 鎺ㄨ崘 prompt 鍙兘鍩轰簬杈撳叆浜嬪疄瑙ｉ噴鐞嗙敱銆?- 涓嶅厑璁哥紪閫犻」鐩€佷环鏍笺€佹椂闀裤€佹妧甯堝拰鎺掔彮銆?- 鎺ㄨ崘鏈嶅姟鏃跺繀椤荤粰鍑衡€滀负浠€涔堥€傚悎褰撳墠鐥囩姸/鍋忓ソ鈥濄€?
楠屾敹鏍囧噯锛?
- 鈥滆叞閰歌儗鐥涙帹鑽愰」鐩€濊蛋 Recommendation Agent銆?- 鈥滀綘浠湁鍝簺椤圭洰鈥濅粛璧?Knowledge Agent銆?- 椤圭洰鎺ㄨ崘鍚庣殑鍚庣画棰勭害鑳界户鎵挎帹鑽愰」鐩€?- 鎶€甯堟帹鑽愬繀椤诲熀浜庡疄鏃跺彲绾﹀€欓€夋睜銆?
---

### 闃舵鍗侊細Knowledge / Availability / Booking Agent 瀵归綈鏂板绾?
鐩爣锛?
- 璁╃幇鏈?consultation銆乤vailability銆乥ooking 涓夋潯閾捐矾閫傞厤鏂扮殑澶?Agent 濂戠害銆?
Knowledge Agent锛?
```text
褰撳墠 consultation Specialist -> 鐩爣 Knowledge Agent
鐭湡淇濈暀 consultation 鐩綍鍚嶏紝鏂囨。鍜?contract 涓爣娉?alias銆?鍚庣画鍙€夐噸鍛藉悕涓?knowledge銆?```

Knowledge 瑕佹眰锛?
- 闈欐€佸挩璇€佹湇鍔＄洰褰曘€佸湴鍧€銆佷环鏍笺€佽惀涓氭椂闂磋蛋 Knowledge銆?- 杈撳嚭 `knowledge_result.v1`銆?- 鍙敤 RAG + LLM 缁勭粐鍥炵瓟锛屼絾浜嬪疄蹇呴』鏉ヨ嚜鐭ヨ瘑搴撴垨閰嶇疆銆?
Availability 瑕佹眰锛?
- 鍙礋璐ｆ帓鐝簨瀹炲拰鍊欓€夋睜銆?- 杈撳嚭 `availability_result.v1`銆?- 涓嶇洿鎺ュ喅瀹氭槸鍚︽帹鑽愭垨棰勭害銆?
Booking 瑕佹眰锛?
- 淇濇寔纭畾鎬?workflow銆?- 杈撳嚭 `booking_result.v1`銆?- Booking draft 浠?`shared_focus_context` 琛ラ綈锛屼絾鍐欏叆鍓嶅繀椤讳互 Booking draft 涓哄噯銆?- 纭鍗曞瓧娈垫潵鑷?Booking contract锛學riter 涓嶈兘鏀瑰啓銆?
宸ュ叿璋冪敤瑕佹眰锛?
- Knowledge 鍙敤璇诲伐鍏枫€?- Availability 鍙敤璇诲伐鍏枫€?- Booking 鏄敮涓€鍙皟鐢ㄩ绾﹀啓宸ュ叿鐨?Agent銆?
楠屾敹鏍囧噯锛?
- 涓変釜 Agent 閮借緭鍑烘爣鍑?AgentResult銆?- Booking 涓嶇粫杩囩己妲戒綅銆佺‘璁ゅ拰 Guard銆?- Availability 涓嶇洿鎺ユ帹鍔ㄥ悗缁矾鐢憋紝鍙繑鍥炲€欓€夋睜鍜屽彲閫夊缓璁换鍔°€?
---

### 闃舵鍗佷竴锛歅rompt 浣撶郴涓庤緭鍑烘牎楠屾不鐞?
鐩爣锛?
- 鎵€鏈?LLM prompt 閮芥湁鏄庣‘鑱岃矗銆佽緭鍏ャ€佽緭鍑?schema 鍜屽け璐ュ厹搴曘€?- 閬垮厤鈥滀竴涓ぇ prompt 璐熻矗鎵€鏈夋祦绋嬧€濄€?
寤鸿鐩綍锛?
```text
agents/understander/prompts.py
agents/supervisor/prompts.py
agents/specialists/recommendation/prompts.py
agents/specialists/consultation/prompts.py
agents/response_writer/prompts.py
```

Prompt 鍒嗙被锛?
```text
Understanding fallback prompt
  杈撳叆锛氱敤鎴锋枃鏈€佽交閲忎笂涓嬫枃
  杈撳嚭锛歍askFrame compatible JSON

Supervisor planner prompt
  杈撳叆锛歍askFrame銆佷笂涓嬫枃鎽樿銆佸彲鐢?agent/action 鐧藉悕鍗?  杈撳嚭锛欵xecutionPlan JSON

Supervisor reviewer prompt
  杈撳叆锛氳鍒掓憳瑕併€丄gentResult 鎽樿
  杈撳嚭锛歝ontinue/wait/complete/blocked/append task

Recommendation prompt
  杈撳叆锛氭湇鍔＄洰褰?鎶€甯堝€欓€夋睜/鐢ㄦ埛鍋忓ソ
  杈撳嚭锛氭帹鑽愮悊鐢辨垨鎺掑簭瑙ｉ噴

Knowledge RAG prompt
  杈撳叆锛氭绱㈡枃妗ｃ€佺敤鎴烽棶棰?  杈撳嚭锛氬熀浜庤祫鏂欑殑鍥炵瓟

Response writer prompt
  杈撳叆锛欵xecutionPlan銆乼urn_results銆乶ext_expected_user_action
  杈撳嚭锛氭渶缁堢敤鎴峰洖澶?```

杈撳嚭鏍￠獙锛?
- 鎵€鏈?JSON prompt 蹇呴』 schema validate銆?- 鏍￠獙澶辫触鏈€澶氶噸璇曚竴娆°€?- 鍐嶅け璐ヨ繘鍏ョ‘瀹氭€?fallback銆?- Booking 鐩稿叧鍏抽敭浜嬪疄涓嶅厑璁哥敱 Writer 閲嶆柊鐢熸垚銆?
楠屾敹鏍囧噯锛?
- 姣忎釜 LLM 璋冪敤鐐归兘鏈夊崟鐙?prompt 鍜?schema銆?- LLM 杈撳嚭涓嶈兘缁曡繃宸ュ叿銆佺姸鎬佸拰 Guard銆?- prompt 澶辫触鏃剁郴缁熶粛鑳界粰鍑哄彲鎺у洖澶嶃€?
---

### 闃舵鍗佷簩锛歊esponse Writer 鐙珛鍖?
鐩爣锛?
- 鏈€缁堝洖澶嶄粠 Supervisor 鍐呴儴 response node 鎶借薄涓虹嫭绔?Writer銆?- 澶?Agent 缁撴灉鐢?Writer 缁熶竴缁勭粐锛屼笉鍐嶅嚭鐜板涓満鍣ㄤ汉鍓茶鍥炲銆?
寤鸿钀界偣锛?
```text
agents/response_writer/
  schema.py
  writer.py
  prompts.py
```

鐭湡鍏煎锛?
```text
agents/supervisor/response_node.py
agents/response_writer/composer.py
```

Writer 杈撳叆锛?
```python
WriterInput = {
    "execution_plan": {},
    "turn_results": [],
    "shared_focus_context": {},
    "completion_reason": None,
    "next_expected_user_action": None,
}
```

Writer 绛栫暐锛?
```text
completed
  姹囨€诲畬鎴愮粨鏋溿€?
waiting_user
  鏄庣‘鍛婅瘔鐢ㄦ埛闇€瑕佽ˉ浠€涔堟垨纭浠€涔堛€?
blocked
  璇存槑闃诲鍘熷洜锛屽苟缁欏嚭鍙户缁緭鍏ユ柟寮忋€?
failed
  璇存槑澶辫触鍘熷洜鍜屾仮澶嶅缓璁€?```

瀹夊叏绾︽潫锛?
- 涓嶆敼鍐?Booking 鏃堕棿銆侀」鐩€佹妧甯堛€佷环鏍笺€?- 涓嶇紪閫犳帓鐝€佷环鏍笺€佸湴鍧€銆?- 瀵?Booking confirmation / booking_created 浣跨敤妯℃澘浼樺厛銆?- 涓嶆毚闇插涓?Agent 韬唤锛岄櫎闈炶皟璇曟ā寮忛渶瑕併€?
楠屾敹鏍囧噯锛?
- 澶?Agent 鎵ц鍚庡彧杈撳嚭涓€涓粺涓€鍥炲銆?- 鏌ヨ + 鎺ㄨ崘 + 棰勭害鎵挎帴涓嶄細閲嶅鎴栦簰鐩歌鐩栥€?- Booking 鍏抽敭瀛楁绋冲畾銆?
---

### 闃舵鍗佷笁锛歀LM Planner / Plan Reviewer 鍙楁帶澧炲己

鐩爣锛?
- 鍦ㄧ‘瀹氭€?Planner 绋冲畾鍚庯紝寮曞叆鍙楁帶 LLM Planner 鍜?Reviewer锛屾彁鍗囧鏉傚鎰忓浘浠诲姟鑳藉姏銆?
鏂板/淇敼锛?
```text
agents/supervisor/planner.py
agents/supervisor/plan_reviewer.py
agents/supervisor/prompts.py
```

瑙﹀彂鏉′欢锛?
```text
瑙勫垯鏃犳硶纭畾璁″垝
澶氭剰鍥剧粍鍚堣秴杩囩‘瀹氭€ф槧灏勮兘鍔?瀛?Agent 缁撴灉鍜岀敤鎴风洰鏍囦箣闂村瓨鍦ㄥ鏉傚樊璺?鐢ㄦ埛鎻愬嚭璺ㄥ涓鍩熺殑澶嶅悎璇锋眰
```

杈撳叆闄愬埗锛?
- 鍙紶鍏ュ繀瑕佺姸鎬佹憳瑕侊紝涓嶄紶鍏ㄩ噺鏁版嵁搴撳拰闀垮巻鍙层€?- 鎻愪緵 agent/action 鐧藉悕鍗曘€?- 鎻愪緵瀹夊叏瑙勫垯锛欱ooking 鍐欐搷浣滃繀椤荤‘璁ゅ拰 Guard銆?
杈撳嚭闄愬埗锛?
- 鍙兘杈撳嚭 `ExecutionPlan` 鎴?plan patch銆?- 涓嶈兘鐩存帴璋冪敤宸ュ叿銆?- 涓嶈兘鐢熸垚鏈煡 agent/action銆?- 涓嶈兘鐢熸垚鍗遍櫓鍐欎换鍔°€?
楠屾敹鏍囧噯锛?
- 绠€鍗曚换鍔′笉璋冪敤 LLM Planner銆?- 澶嶆潅浠诲姟鍙敓鎴愬悎鐞嗗姝ヨ鍒掋€?- LLM 杈撳嚭閿欒鏃惰兘瀹夊叏闄嶇骇銆?- Booking 瀹夊叏杈圭晫涓嶅彈 LLM 褰卞搷銆?
---

### 闃舵鍗佸洓锛歍race銆佸彲瑙傛祴涓庤皟璇曡鍥?
鐩爣锛?
- 姣忔澶?Agent 鎵ц閮藉彲瑙ｉ噴銆佸彲澶嶇幇銆佸彲璋冭瘯銆?
鏂板/淇敼锛?
```text
api/graph_state_view.py
services/session_state_store.py
agents/supervisor/trace.py
```

Trace 瀛楁锛?
```text
understanding_source
task_frame_summary
plan_id
plan_source
plan_status
current_task_id
executed_tasks
skipped_tasks
agent_results
tool_calls
suggested_next_tasks
accepted_next_tasks
rejected_next_tasks
completion_reason
writer_input_summary
```

鍙娴嬭姹傦細

- 鑳界湅鍒版瘡涓€姝ヤ负浠€涔堣皟鐢ㄦ煇涓?Agent銆?- 鑳界湅鍒板瓙 Agent 璋冪敤浜嗗摢浜涘伐鍏枫€?- 鑳界湅鍒颁负浠€涔堢户缁€佺瓑寰呯敤鎴锋垨缁撴潫銆?- 鑳界湅鍒?Writer 娑堣垂浜嗗摢浜涚粨鏋溿€?
楠屾敹鏍囧噯锛?
- 璋冭瘯瑙嗗浘鍙睍绀哄畬鏁磋鍒掑拰鎵ц缁撴灉銆?- Trace 涓嶆硠婕忔晱鎰熷師濮嬫暟鎹€?- 姣忎釜澶辫触鍦烘櫙鑳藉畾浣嶅け璐?Agent銆佸伐鍏锋垨 prompt銆?
---

### 闃舵鍗佷簲锛氳瘎娴嬨€佸洖褰掍笌鏂囨。鍚屾

鐩爣锛?
- 鐢ㄦ祴璇曚繚璇佺郴缁熷凡缁忕湡姝ｈ浆鍙樹负棰勬湡澶氭櫤鑳戒綋鏋舵瀯銆?
娴嬭瘯鏂瑰悜锛?
```text
Understanding tests
  - 瑙勫垯鍛戒腑
  - 涓婁笅鏂囨壙鎺?  - LLM 鍏滃簳 schema

Planner tests
  - TaskFrame -> ExecutionPlan
  - 澶氭剰鍥?query-first plan
  - 鎺ㄨ崘鎵挎帴 booking plan

Controller tests
  - next task selection
  - task status update
  - turn_results result_ref

Agent contract tests
  - knowledge_result.v1
  - availability_result.v1
  - recommendation_result.v1
  - booking_result.v1

Safety tests
  - 鏈‘璁や笉鍒涘缓棰勭害
  - 涓嶅彲绾︿笉鍒涘缓棰勭害
  - LLM 涓嶈兘鐢熸垚鍗遍櫓鍐欎换鍔?
End-to-end tests
  - 椤圭洰鎺ㄨ崘 -> 鎶€甯堟帹鑽?-> 閫夋嫨 -> 棰勭害纭
  - 鏌ヨ + 鎺ㄨ崘 + 棰勭害澶嶅悎浠诲姟
  - 鎹㈡帹鑽?  - 淇敼鏃堕棿鍚庡€欓€夋睜鍜岀‘璁ゅ崟澶辨晥
```

鏂囨。鍚屾锛?
```text
README.md
ARCHITECTURE_3_0.md
MATURE_AGENT_LAYER_FRAMEWORK.md
MULTI_AGENT_REFACTOR_PLAN.md
```

楠屾敹鏍囧噯锛?
- 鏍稿績鍗曟祴鍜岀鍒扮娴嬭瘯閫氳繃銆?- README 鍚姩鏂瑰紡浠嶅彲鐢ㄣ€?- 鏋舵瀯鏂囨。鍜屽疄闄呭疄鐜颁竴鑷淬€?- 鍏稿瀷瀵硅瘽閾捐矾杈惧埌棰勬湡澶氭櫤鑳戒綋琛屼负銆?
---

## 9. 闇€瑕侀噸鐐逛慨澶嶇殑鍏稿瀷閾捐矾

### 9.1 椤圭洰鎺ㄨ崘鍚庢壙鎺ユ妧甯堟帹鑽?
鐩爣閾捐矾锛?
```text
鐢ㄦ埛锛氭垜鑵伴吀鑳岀棝锛屼綘鏈変粈涔堟帹鑽愮殑椤圭洰鍚?Understanding -> service_recommendation
Supervisor Plan -> recommendation.recommend_service
Recommendation -> 鎺ㄨ崘鑳岄儴鎺ㄦ嬁锛屽苟鍐欏叆 focus.service_type
Writer -> 杈撳嚭椤圭洰鎺ㄨ崘

鐢ㄦ埛锛氭垜鎯虫槑澶╀笅鍗堜笁鐐瑰幓锛屼綘鏈夋帹鑽愮殑鎶€甯堝悧
Understanding -> technician_recommendation + start_time
Supervisor Plan -> availability.query_availability -> recommendation.recommend_technician
Availability -> 杩斿洖鍙害鎶€甯?Recommendation -> 鎺ㄨ崘鎶€甯?Writer -> 杈撳嚭鎶€甯堟帹鑽?
鐢ㄦ埛锛氭垜閫夌帇寮哄惂
Understanding -> recommendation_selection
Supervisor Plan -> booking.select_recommended_technician -> booking.start_or_continue_booking
Booking -> 鍚堝苟 service_type/start_time/technician
Writer -> 濡傛灉妲戒綅瀹屾暣锛岃緭鍑洪绾︾‘璁わ紱濡傛灉缂烘椂闀匡紝璇㈤棶鏃堕暱
```

閬垮厤鐨勯棶棰橈細

- 涓嶅簲璇ュ洜涓衡€滃氨浠栧惂鈥濅涪澶变箣鍓嶆帹鑽愮殑鏈嶅姟椤圭洰銆?- 涓嶅簲璇ョ敱 Recommendation Agent 鑷繁鍐冲畾杩涘叆 Booking銆?- 涓嶅簲璇?Booking 鍙嬁鍒版妧甯堬紝鍗翠涪澶遍」鐩拰鏃堕棿銆?
### 9.2 鏌ヨ涓庨绾?鎺ㄨ崘骞跺瓨

鐩爣绛栫暐锛?
- 鏌ヨ绫讳换鍔″厛鍥炵瓟鎴栧厛浜у嚭浜嬪疄銆?- 鍚庣画棰勭害/鎺ㄨ崘浠诲姟缁х画鎵ц銆?- 鏈€缁堢敱 Writer 缁熶竴缁勭粐锛屼笉杈撳嚭澶氭鍓茶鐨勬満鍣ㄤ汉鍥炲銆?
绀轰緥锛?
```text
鐢ㄦ埛锛氫綘浠湁浠€涔堥」鐩紵鎴戞兂涓嬪崍浜旂偣鍋氬叏韬帹鎷匡紝鏈夋帹鑽愭妧甯堝悧
Plan:
  1. knowledge.answer_service_catalog
  2. availability.query_availability
  3. recommendation.recommend_technician
  4. writer.final_answer
```

---

## 10. 涓嶅缓璁仛鐨勪簨

- 涓嶅缓璁 Specialist 鑷繁鍐冲畾涓嬩竴涓?Agent銆?- 涓嶅缓璁瀛?Agent 鐩存帴鏀瑰啓涓嬩竴姝ヨ矾鐢便€?- 涓嶅缓璁 Booking 鍙樻垚鑷敱 LLM Agent銆?- 涓嶅缓璁敤鑷劧璇█鍥炲浣滀负 Agent 闂翠氦鎺ヤ緷鎹€?- 涓嶅缓璁妸鎵€鏈夌姸鎬佸杩涗竴涓ぇ prompt锛岃妯″瀷鑷敱鍒ゆ柇娴佺▼銆?- 涓嶅缓璁竴寮€濮嬪氨鎶婃墍鏈夊瓙 Agent 鏀归€犳垚瀹屽叏鑷富 Tool Agent銆?
---

## 11. 鎺ㄨ崘瀹炴柦椤哄簭

寤鸿涓ユ牸鎸変互涓嬮『搴忔帹杩涖€傝繖涓『搴忕殑璁捐鍘熷垯鏄細鍏堝浐鍖栧熀绾匡紝鍐嶈皟鏁寸姸鎬佸拰涓婁笅鏂囷紝鐒跺悗鏀硅鍒掍笌鎵ц锛屾渶鍚庡啀寮曞叆鏇村己鐨?LLM 缂栨帓鑳藉姏銆?
```text
0. 鍩虹嚎姊崇悊涓庡洖褰掍繚鎶?1. 鐘舵€佷笌涓婁笅鏂囧绾﹂噸鏋?2. 鎰忓浘鐞嗚В杈撳嚭瀵归綈澶?Agent 璁″垝
3. 寮曞叆 ExecutionPlan 涓庣‘瀹氭€?Planner
4. 宸ュ叿璋冪敤灞備笌宸ュ叿濂戠害鏁寸悊
5. Controller 鎸夎鍒掕皟鐢ㄥ瓙 Agent
6. 缁熶竴瀛?Agent 缁撴灉濂戠害
7. Completion Checker 涓庤鍒掍慨姝?8. 寤鸿浠诲姟娌荤悊锛岀粺涓€涓?suggested_next_tasks
9. Recommendation Agent 鎵╁睍涓虹粺涓€鎺ㄨ崘 Agent
10. Knowledge / Availability / Booking Agent 瀵归綈鏂板绾?11. Prompt 浣撶郴涓庤緭鍑烘牎楠屾不鐞?12. Response Writer 鐙珛鍖?13. LLM Planner / Plan Reviewer 鍙楁帶澧炲己
14. Trace銆佸彲瑙傛祴涓庤皟璇曡鍥?15. 璇勬祴銆佸洖褰掍笌鏂囨。鍚屾
```

鎵ц鍘熷垯锛?
- 姣忎竴闃舵閮藉繀椤绘湁娴嬭瘯鎴栨墜宸ラ獙璇佺偣锛屼笉鍏佽鍙敼缁撴瀯涓嶉獙璇侀摼璺€?- 浠讳綍娑夊強 Booking 鍐欐搷浣滅殑闃舵锛岄兘蹇呴』鍏堥獙璇佺‘璁ゃ€丟uard 鍜屽箓绛夎竟鐣屻€?- 浠讳綍娑夊強 LLM 鐨勯樁娈碉紝閮藉繀椤诲厛鏈?schema 鏍￠獙鍜屽け璐ュ厹搴曘€?- 鍏堝仛纭畾鎬х増鏈紝鍐嶅仛 LLM 澧炲己鐗堟湰銆?- 鏃у瓧娈靛厛鍏煎淇濈暀锛岀瓑鏂伴摼璺ǔ瀹氬悗鍐嶈縼绉绘垨搴熷純銆?
---

## 12. 绗竴鎵瑰缓璁慨鏀逛换鍔?
### 绗竴鎵癸細鐘舵€併€佷笂涓嬫枃銆佸熀绾?
```text
1. 姊崇悊骞惰褰曞綋鍓嶄富閾捐矾鍜屾牳蹇冪姸鎬佸瓧娈点€?2. 澧炲姞鎴栬ˉ榻愬洖褰掔敤渚嬶細闈欐€佸挩璇€侀」鐩帹鑽愩€佹帓鐝€佹妧甯堟帹鑽愩€佹帹鑽愭壙鎺ラ绾︺€丅ooking Guard銆?3. 鏂板 shared context schema / context manager銆?4. 鎵╁睍 shared_focus_context 瀛楁锛歴ymptom_or_need銆乺ecommended_service銆乻elected_recommendation_ref銆乧ontext_source銆乽pdated_by銆乽pdated_at銆?5. 澧炲姞涓婁笅鏂囧け鏁堣鍒欙細淇敼鏃堕棿/椤圭洰/鎶€甯堝悗锛屾竻鐞嗕緷璧栨棫鏉′欢鐨勬帓鐝€佹帹鑽愩€佺‘璁ゅ崟銆?6. 鏇存柊 session_state_store 鍜?graph_state_view锛岀‘淇濇柊涓婁笅鏂囧瓧娈靛彲鎸佷箙鍖栥€佸彲瑙傚療銆?```

绗竴鎵归獙鏀讹細

```text
1. 涓嶆敼鍙樺綋鍓嶇敤鎴峰彲瑙佽涓恒€?2. 涓婁笅鏂囨壙鎺ラ摼璺彲閫氳繃鐘舵€佹煡鐪嬨€?3. 淇敼鍏抽敭妲戒綅鍚庝笉浼氱户缁娇鐢ㄨ繃鏈熷€欓€夋睜鎴栨棫纭鍗曘€?4. 鍥炲綊鐢ㄤ緥鑳戒綔涓哄悗缁敼閫犲熀绾裤€?```

### 绗簩鎵癸細鎰忓浘鐞嗚В涓庤鍒掗鏋?
```text
1. 瀵归綈 TaskFrame 杈撳嚭瀛楁锛歵ask_type銆乸rimary_intent銆乻econdary_intents銆乻lots銆乵issing_slots銆乧ontext_links銆乧onfidence銆乻ource銆乶eeds_planning銆乹uery_first銆?2. 琛ラ綈浠诲姟绫诲瀷锛歬nowledge_consultation銆乤vailability_query銆乻ervice_recommendation銆乼echnician_recommendation銆乺ecommendation_selection銆乥ooking_creation銆乥ooking_confirmation 绛夈€?3. 璋冩暣 LLM fallback prompt锛屼娇鍏惰緭鍑?TaskFrame-compatible JSON锛岃€屼笉鏄嚜鐢辫矾鐢便€?4. 鏂板 agents/supervisor/plan_schema.py銆?5. 鍦?SupervisorState 涓鍔?execution_plan銆?6. 鏂板 agents/supervisor/planner.py锛屽厛鍋氱‘瀹氭€?TaskFrame -> ExecutionPlan 鏄犲皠銆?```

绗簩鎵归獙鏀讹細

```text
1. 姣忚疆閮芥湁 TaskFrame 鍜?execution_plan銆?2. 鈥滆叞閰歌儗鐥涙帹鑽愰」鐩€濈敓鎴?recommendation.recommend_service銆?3. 鈥滄槑澶╀笅鍗堜笁鐐规帹鑽愭妧甯堚€濈敓鎴?availability.query_availability -> recommendation.recommend_technician銆?4. 鈥滃氨浠栧惂鈥濈敓鎴?booking.select_recommended_technician -> booking.start_or_continue_booking銆?5. route_decision 淇濈暀鍏煎锛屼絾涓嶅啀浣滀负闀挎湡涓昏璁°€?```

### 绗笁鎵癸細宸ュ叿濂戠害銆丆ontroller銆佺粨鏋滃绾?
```text
1. 姊崇悊宸ュ叿鍒嗙被锛欿nowledge 璇诲伐鍏枫€丄vailability 璇诲伐鍏枫€丷ecommendation 鎺掑簭宸ュ叿銆丅ooking 鍐欏伐鍏枫€?2. 瀹氫箟 ToolResult 濂戠害鍜?Booking 鍐欏伐鍏峰畨鍏ㄨ竟鐣屻€?3. 鏂板 agents/supervisor/controller.py銆?4. Controller 鏍规嵁 execution_plan.current_task 璋冪敤瀛?Agent銆?5. turn_results 鍜?execution_plan.tasks[].result_ref 寤虹珛鏄犲皠銆?6. 缁熶竴 AgentResult 濂戠害锛歷ersion銆乤gent_name銆乻tatus銆乺esult_type銆乫acts銆乻tate_updates銆乼ool_results銆乺equires_user_input銆乻uggested_next_tasks銆?```

绗笁鎵归獙鏀讹細

```text
1. Supervisor 涓嶇洿鎺ヨ皟鐢ㄤ笟鍔″伐鍏枫€?2. 瀛?Agent 宸ュ叿缁撴灉鍙互閫氳繃 AgentResult 鍜?tool_results 杩借釜銆?3. 澶氭浠诲姟鍙互鐢?execution_plan 鑷姩鎺ㄨ繘銆?4. Booking 鍐欏伐鍏蜂粛蹇呴』缁忚繃纭銆丟uard 鍜屽箓绛変繚鎶ゃ€?```

### 绗洓鎵癸細Completion銆佸缓璁换鍔℃不鐞嗐€佹帹鑽?Agent 鎵╁睍

```text
1. 鏂板 completion.py锛屾牴鎹?AgentResult 鍒ゆ柇 continue / waiting_user / completed / blocked / failed銆?2. 瀛?Agent 鍚庣画寤鸿缁熶竴涓?suggested_next_tasks銆?3. Supervisor 鏍￠獙 suggested_next_tasks 鍚庡啀杩藉姞鍒?execution_plan锛屽苟璁板綍 accepted/rejected review銆?4. Recommendation Agent 澧炲姞 recommend_service銆?5. 椤圭洰鎺ㄨ崘缁撴灉鍐欏叆 shared_focus_context.service_type / recommended_service銆?6. 鎶€甯堟帹鑽愬繀椤绘秷璐?Availability 鍊欓€夋睜銆?7. 鈥滄崲涓€涓€濅娇鐢ㄦ帓闄ゅ垪琛紝涓嶆薄鏌?Booking draft銆?```

绗洓鎵归獙鏀讹細

```text
1. 瀛?Agent 涓嶅啀鍐冲畾涓嬩竴姝ヨ矾鐢便€?2. Recommendation 瀹屾垚鍚庣瓑寰呯敤鎴锋帴鍙楋紝涓嶈嚜鍔ㄥ垱寤洪绾︺€?3. 椤圭洰鎺ㄨ崘鍚庤兘鑷劧鎵挎帴鎶€甯堟帹鑽愬拰棰勭害銆?4. 淇敼鏃堕棿/椤圭洰鍚庯紝鎺ㄨ崘鍜岀‘璁ゅ崟鑳芥纭け鏁堝苟閲嶅缓銆?```

### 绗簲鎵癸細Prompt銆乄riter銆丩LM 缂栨帓澧炲己

```text
1. 姊崇悊骞舵媶鍒?prompt锛歶nderstanding fallback銆乻upervisor planner銆乻upervisor reviewer銆乺ecommendation銆乲nowledge RAG銆乺esponse writer銆?2. 鎵€鏈?JSON prompt 澧炲姞 schema 鏍￠獙鍜屽け璐ュ厹搴曘€?3. Response Writer 鐙珛鍖栵紝缁熶竴娑堣垂 execution_plan + turn_results + shared_focus_context銆?4. Booking confirmation / booking_created 浣跨敤妯℃澘浼樺厛銆?5. 寮曞叆鍙楁帶 LLM Planner锛屽彧鍦ㄥ鏉傚鎰忓浘鎴栬鍒欐棤娉曡鍒掓椂鍚敤銆?6. 寮曞叆鍙楁帶 Plan Reviewer锛屽彧杈撳嚭 continue/wait/complete/blocked/append_allowed_task銆?```

绗簲鎵归獙鏀讹細

```text
1. 绠€鍗曚换鍔′笉璋冪敤 LLM Planner銆?2. 澶嶆潅浠诲姟鍙敓鎴愬悎鐞嗗姝ヨ鍒掋€?3. Writer 鍙緭鍑轰竴涓粺涓€鍥炲銆?4. LLM 涓嶈兘缁曡繃 Booking 纭銆丟uard 鍜屽啓宸ュ叿濂戠害銆?```

### 绗叚鎵癸細Trace銆佽瘎娴嬨€佹枃妗ｅ悓姝?
```text
1. Trace 澧炲姞 understanding_source銆乸lan_id銆乧urrent_task_id銆乪xecuted_tasks銆乼ool_calls銆乻uggested/accepted/rejected next tasks銆乧ompletion_reason銆亀riter_input_summary銆?2. 澧炲姞绔埌绔祴璇曪細椤圭洰鎺ㄨ崘 -> 鎶€甯堟帹鑽?-> 閫夋嫨 -> 棰勭害纭銆?3. 澧炲姞 query-first 澶嶅悎浠诲姟娴嬭瘯銆?4. 澧炲姞 Booking 瀹夊叏娴嬭瘯銆?5. 鏇存柊 README銆丄RCHITECTURE_3_0銆丮ATURE_AGENT_LAYER_FRAMEWORK銆?```

绗叚鎵归獙鏀讹細

```text
1. 姣忎釜澶?Agent 鍥炲悎閮藉彲瑙ｉ噴銆佸彲澶嶇幇銆?2. 鏍稿績娴嬭瘯閫氳繃銆?3. 鏂囨。鍜屽疄闄呭疄鐜颁竴鑷淬€?4. 绯荤粺琛屼负绗﹀悎鏈€缁堝鏅鸿兘浣撲富绾裤€?```

---

## 13. 鏈€缁堥獙鏀舵爣鍑?
瀹屾垚鏀归€犲悗锛岀郴缁熷簲婊¤冻锛?
- 姣忎釜鐢ㄦ埛鍥炲悎閮芥湁娓呮櫚 `TaskFrame` 鍜?`ExecutionPlan`銆?- Supervisor 鑳借В閲婁负浠€涔堣皟鐢ㄦ煇涓瓙 Agent銆?- 瀛?Agent 鍙繑鍥炵粨鏋勫寲缁撴灉鍜屽缓璁紝涓嶇洿鎺ュ喅瀹氫笅涓€姝ヨ矾鐢便€?- Supervisor 鑳芥牴鎹瓙 Agent 缁撴灉缁х画璋冪敤銆佺瓑寰呯敤鎴枫€佸け璐ユ仮澶嶆垨缁撴潫銆?- Response Writer 杈撳嚭缁熶竴鑷劧璇█鍥炲銆?- Recommendation Agent 鍚屾椂鏀寔椤圭洰鎺ㄨ崘鍜屾妧甯堟帹鑽愩€?- Booking 鍐欐搷浣滀粛鐢辩‘瀹氭€ф祦绋嬨€佺‘璁ゅ拰 Guard 鎺у埗銆?- 澶氭剰鍥俱€乹uery-first銆佹帹鑽愭壙鎺ラ绾︺€佹崲鎺ㄨ崘銆佺‘璁ら绾﹂兘鑳界ǔ瀹氳繍琛屻€?
