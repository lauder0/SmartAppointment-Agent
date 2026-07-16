# Smart Appointment 鎴愮啛 Agent 鍒嗗眰寤鸿妗嗘灦

鏈枃妗ｇ敤浜庢寚瀵?Smart Appointment 3.0 浠庘€滃姛鑳藉彲鐢ㄢ€濋€愭婕旇繘涓衡€滄垚鐔?Agent 宸ョ▼椤圭洰鈥濄€傛鏋剁粨鍚堝綋鍓嶉」鐩疄鐜般€併€婃垚鐔?Agent 椤圭洰寤鸿鎸囧崡.md銆嬨€乣goal.md` 涓殑鑳藉姏鐩爣锛屼互鍙?Agent 宸ョ▼瀹炶返缁忛獙鏁寸悊鑰屾垚銆?
鏍稿績鎬濊矾鏄細涓嶈鍙寜鎶€鏈ā鍧楁媶椤圭洰锛岃€岃鎸?**Agent 鐨勫畬鏁磋繍琛岄摼璺?+ 宸ョ▼娌荤悊鑳藉姏** 鏉ユ媶銆傛瘡涓€灞傞兘搴旇鍥炵瓟涓変釜闂锛?
- 杩欎竴灞傝礋璐ｄ粈涔堬紵
- 褰撳墠椤圭洰宸茬粡鍋氬埌浠€涔堬紵
- 涓嬩竴姝ュ簲璇ヨˉ浠€涔堬紵

鎺ㄨ崘灏嗛」鐩媶鎴?15 涓眰娆★細

```text
0. 涓氬姟鐩爣涓庢垚鍔熸寚鏍囧眰
   鈫?1. 鐢ㄦ埛鍏ュ彛涓庝氦浜掍綋楠屽眰
   鈫?2. 鎰忓浘鐞嗚В涓庝换鍔″缓妯″眰
   鈫?3. 瀵硅瘽涓婁笅鏂囦笌妲戒綅绠＄悊灞?   鈫?4. Agent 缂栨帓涓庝换鍔℃祦杞眰
   鈫?5. 棰嗗煙 Agent / Specialist 鑳藉姏灞?   鈫?6. 宸ュ叿璋冪敤涓庝笟鍔℃湇鍔″眰
   鈫?7. 鐭ヨ瘑搴撲笌 RAG 灞?   鈫?8. 璁板繂涓庣姸鎬佹寔涔呭寲灞?   鈫?9. Prompt 涓庝笂涓嬫枃宸ョ▼灞?   鈫?10. 瀹夊叏銆佹潈闄愪笌 Guardrail 灞?   鈫?11. 绋冲畾鎬с€佸紓甯告仮澶嶄笌骞傜瓑灞?   鈫?12. 鍙娴嬨€佹棩蹇椾笌 Trace 灞?   鈫?13. 璇勬祴銆佸疄楠屼笌鎸佺画杩唬灞?   鈫?14. 閮ㄧ讲銆佽繍缁翠笌鎴愭湰娌荤悊灞?```

---

## 0. 涓氬姟鐩爣涓庢垚鍔熸寚鏍囧眰

杩欎竴灞傛槸鎵€鏈?Agent 椤圭洰鐨勫湴鍩恒€?
鏍稿績闂锛?
```text
杩欎釜 Agent 鍒板簳瑙ｅ喅浠€涔堜笟鍔￠棶棰橈紵
浠€涔堝彨鍋氬仛寰楀ソ锛?浠€涔堝彨鍋氬け璐ワ紵
```

瀵?Smart Appointment 鏉ヨ锛屼笟鍔＄洰鏍囦笉鏄€滃仛涓€涓亰澶╂満鍣ㄤ汉鈥濓紝鑰屾槸锛?
```text
闈㈠悜鎸夋懇闂ㄥ簵鐨勬櫤鑳介绾?Agent锛?鑳藉畬鎴愭湇鍔″挩璇€佹妧甯堟帹鑽愩€佹帓鐝煡璇€侀绾﹀垱寤恒€佺敤鎴峰亸濂芥矇娣€涓庡鐢ㄣ€?```

寤鸿瀹氫箟浠ヤ笅鎸囨爣锛?
- **浠诲姟鎴愬姛鐜?*锛氱敤鎴蜂粠鍜ㄨ鍒版垚鍔熷畬鎴愮洰鏍囦换鍔＄殑姣斾緥銆?- **棰勭害杞寲鐜?*锛氱敤鎴峰挩璇㈡湇鍔″悗杩涘叆棰勭害纭鎴栨垚鍔熼绾︾殑姣斾緥銆?- **鎺ㄨ崘鎺ュ彈鐜?*锛氭帹鑽愭妧甯堝悗鐢ㄦ埛鎺ュ彈鎺ㄨ崘鐨勬瘮渚嬨€?- **澶氳疆瀹屾垚鐜?*锛氳法澶氳疆琛ユЫ鍚庝粛鑳藉畬鎴愪换鍔＄殑姣斾緥銆?- **閿欒棰勭害鐜?*锛氭椂闂淬€侀」鐩€佹妧甯堛€佹椂闀块敊璇殑姣斾緥銆?- **浜哄伐浠嬪叆鐜?*锛氶渶瑕佷汉宸ュ鐞嗙殑姣斾緥銆?- **骞冲潎瀹屾垚杞**锛氬畬鎴愪竴娆￠绾﹀钩鍧囬渶瑕佸嚑杞璇濄€?- **鍝嶅簲寤惰繜涓庢垚鏈?*锛歅95 寤惰繜銆丩LM token 鎴愭湰銆佸伐鍏疯皟鐢ㄦ垚鏈€?
褰撳墠椤圭洰鍚庣画鍙互灏嗚繖浜涘唴瀹规暣鐞嗕负 `PROJECT_GOAL.md`锛屾垨琛ュ厖鍒?README 鐨勯」鐩洰鏍囬儴鍒嗐€?
---

## 1. 鐢ㄦ埛鍏ュ彛涓庝氦浜掍綋楠屽眰

杩欎竴灞傝礋璐ｇ敤鎴峰浣曡繘鍏ョ郴缁熴€佸浣曞拰 Agent 瀵硅瘽銆佸浣曟劅鐭ヤ换鍔¤繘搴︺€?
褰撳墠椤圭洰宸茬粡鍏峰锛?
```text
Web 椤甸潰
/chat
/chat/stream
/chat/reset
鐭ヨ瘑搴撱€佹妧甯堛€佹帓鐝€佺敤鎴疯涓虹瓑绠＄悊椤甸潰
```

鎴愮啛椤圭洰搴斿叧娉細

- 澶氱鍏ュ彛锛歐eb銆佺Щ鍔ㄧ銆佸皬绋嬪簭銆佸鏈嶅悗鍙般€丄PI銆?- 娴佸紡杈撳嚭锛氱敤鎴疯兘鐪嬪埌 Agent 姝ｅ湪澶勭悊銆?- 浼氳瘽鎭㈠锛氬埛鏂伴〉闈㈡垨閲嶆柊杩涘叆鍚庤兘鎭㈠涓婁笅鏂囥€?- 鏄庣‘鍙嶉锛氭煡璇腑銆佹帹鑽愪腑銆佸緟纭銆侀绾︽垚鍔熴€佸け璐ュ師鍥犮€?- 鐢ㄦ埛鍙帶锛氬厑璁稿彇娑堛€佷慨鏀广€侀噸鏂版帹鑽愩€侀噸缃細璇濄€?- 绠＄悊鍚庡彴锛氶厤缃」鐩€佹妧甯堛€佹帓鐝€佺煡璇嗐€佺敤鎴峰亸濂姐€?
瀵瑰綋鍓嶉」鐩紝寤鸿涓嬩竴姝ヨˉ鍏咃細

```text
鐢ㄦ埛渚э細灞曠ず褰撳墠棰勭害鑽夌鐘舵€?绠＄悊渚э細灞曠ず姣忔 Agent 璺敱閾捐矾鍜屽伐鍏疯皟鐢ㄧ粨鏋?```

---

## 2. 鎰忓浘鐞嗚В涓庝换鍔″缓妯″眰

杩欎竴灞傝礋璐ｇ悊瑙ｇ敤鎴风湡姝ｆ兂瀹屾垚浠€涔堜换鍔★紝鑰屼笉鏄彧鍋氱畝鍗?intent 鍒嗙被銆?
渚嬪鐢ㄦ埛璇达細

```text
鎴戞兂鍋氬叏韬帹鎷匡紝浣犳湁鎺ㄨ崘鐨勬妧甯堝悧
```

杩欏彞璇濆悓鏃跺寘鍚細

- 鏈嶅姟閫夋嫨锛歚鍏ㄨ韩鎺ㄦ嬁`
- 鎺ㄨ崘璇锋眰锛歚鎺ㄨ崘鎶€甯坄

鎴愮啛绯荤粺搴斿皢鍏跺缓妯′负锛?
```json
{
  "primary_intent": "recommend_technician",
  "secondary_intents": ["service_selection"],
  "task_type": "recommendation_before_booking",
  "slots": {
    "service_type": "鍏ㄨ韩鎺ㄦ嬁"
  },
  "missing_slots": ["start_time"],
  "next_action": "ask_time_for_recommendation"
}
```

杩欎竴灞傚缓璁媶鎴愪互涓嬭兘鍔涳細

- **鎰忓浘璇嗗埆**锛氬挩璇€佹煡鎺掔彮銆侀绾︺€佹帹鑽愩€佷慨鏀广€佸彇娑堛€侀棽鑱娿€佽秺鐣岃姹傘€?- **澶嶅悎鎰忓浘璇嗗埆**锛氭湇鍔￠€夋嫨 + 鎺ㄨ崘銆佹煡鏃堕棿 + 鎸囧畾鎶€甯堛€侀绾?+ 鍋忓ソ銆?- **浠诲姟绫诲瀷寤烘ā**锛氬挩璇换鍔°€佹帓鐝换鍔°€佹帹鑽愪换鍔°€侀绾︿换鍔°€佸敭鍚?淇敼浠诲姟銆?- **妲戒綅鎶藉彇**锛氶」鐩€佹椂闂淬€佹椂闀裤€佹妧甯堛€佹€у埆鍋忓ソ銆佹墜娉曞亸濂姐€佺敤鎴疯韩浠姐€?- **浠诲姟浼樺厛绾?*锛氬綋涓€鍙ヨ瘽閲屾湁澶氫釜鎰忓浘鏃讹紝鍒ゆ柇鍝釜鏄富閾捐矾銆?- **缃俊搴︿笌鍏滃簳**锛氫綆缃俊搴︽椂杩介棶锛岃€屼笉鏄‖璺敱銆?
褰撳墠 3.0 宸茬粡灏嗚繖涓€灞傛暣鐞嗕负 **涓夊眰璇嗗埆 + 鍐崇瓥褰掍竴**锛?
```text
Normalizer 鏍囧噯鍖栦笌妲戒綅鍒濇彁鍙?  鈫?Rule Layer 瑙勫垯璇嗗埆
  鈫?Context Resolver 涓婁笅鏂囧寮?  鈫?LLM Planner 鍏滃簳鐞嗚В
  鈫?Decision Builder 鍐崇瓥褰掍竴
  鈫?RouteDecision 杈撳嚭缁?Supervisor
```

褰撳墠瀹炵幇瑕佺偣锛?
- `agents/understander/rules.py` 瀹氫箟纭畾鎬ц鍒欙紝瑕嗙洊闈欐€佸挩璇€佸疄鏃舵帓鐝€侀绾︺€佹帹鑽愩€佷笂涓嬫枃鎿嶄綔鍜屽畨鍏ㄨ秺鐣屻€?- `rule_signals.py` 杈撳嚭缁撴瀯鍖?`IntentSignal`锛屽寘鍚?`intent_group`銆乣subtype`銆乣confidence`銆乣slots`銆?- `contextual_resolver.py` 缁撳悎褰撳墠 booking / recommendation / availability / task_frame 鐘舵€侊紝瑙ｆ瀽鈥滅‘璁も€濃€滄崲涓€涓€濃€滃氨浠栧惂鈥濃€滄垜閫夌帇寮哄惂鈥濈瓑涓婁笅鏂囪〃杈俱€?- `llm_planner.py` 浣跨敤纭畾鎬ч棬鎺э紝鍙湁瑙勫垯涓庝笂涓嬫枃缁撴灉涓?`uncertain` 鎴?`none` 鏃舵墠璋冪敤 LLM銆?- LLM 杈撳嚭涓嶇洿鎺ヨ矾鐢憋紝鍏堢粡杩?`validate_llm_plan()` 鍋?action銆乻lot銆乧onfidence銆乺isk銆佷笂涓嬫枃鏉冮檺绛夋牎楠屻€?- `decision_builder.py` 灏嗚鍒欍€佷笂涓嬫枃銆丩LM 缁撴灉缁熶竴褰掍竴涓哄彲璺敱鐨勭悊瑙ｇ粨鏋滐紝鏀寔缂烘Ы銆侀粯璁ゆ椂闀裤€佸啿绐佹娴嬨€佸鎰忓浘 continuation銆?- `decision_arbiter.py` 涓茶仈鏁存潯鐞嗚В閾捐矾锛屽苟鐢熸垚鏍囧噯 `RouteDecision` 缁?Supervisor銆?
褰撳墠杩欎竴灞傚凡缁忓畬鎴愮涓€闃舵涓婚摼璺敼閫狅紝鍚庣画閲嶇偣搴旀斁鍦ㄨ瘎娴嬭鐩栥€乀race 鍙В閲婂拰澶嶆潅澶氭剰鍥炬牱渚嬫矇娣€涓娿€?
---

## 3. 瀵硅瘽涓婁笅鏂囦笌妲戒綅绠＄悊灞?
杩欎竴灞傝礋璐ｈ褰曠敤鎴峰凡缁忚杩囦粈涔堛€佸綋鍓嶄换鍔¤繕缂轰粈涔堛€佷笅涓€杞簲璇ラ棶浠€涔堛€?
瀹冨拰鎰忓浘鐞嗚В涓嶅悓锛?
- 鎰忓浘鐞嗚В鍥炵瓟锛氱敤鎴锋兂鍋氫粈涔堛€?- 妲戒綅绠＄悊鍥炵瓟锛氬畬鎴愯繖涓换鍔¤繕宸粈涔堜俊鎭€?
瀵归绾﹂」鐩潵璇达紝鏍稿績妲戒綅鍖呮嫭锛?
```text
service_type       椤圭洰
start_time         寮€濮嬫椂闂?duration_minutes   鏃堕暱
technician_id      鎶€甯?ID
technician_name    鎶€甯堝鍚?gender_preference  鎬у埆鍋忓ソ
style_preference   鎵嬫硶鍋忓ソ
user_id            鐢ㄦ埛
confirmation       鏄惁纭
```

鎴愮啛璁捐闇€瑕佹敮鎸侊細

- 澶氳疆琛ユЫ銆?- 鐢ㄦ埛淇敼宸插～妲戒綅銆?- 鐢ㄦ埛涓€旀彃鍏ュ挩璇㈤棶棰樸€?- 鏌ヨ鎺ㄨ崘鏃朵繚鐣?pending intent銆?- 浠庝笂涓€杞湇鍔＄洰褰曠户鎵?service_type銆?- 浠庢帹鑽愮粨鏋滅户鎵?technician_id銆?- 浠庡巻鍙插亸濂借ˉ榛樿鍊硷紝浣嗕笉鑳藉伔鍋锋浛鐢ㄦ埛纭銆?
寤鸿鎶借薄涓?`Task Frame / Dialogue Frame`锛?
```json
{
  "task_id": "booking_20260712_xxx",
  "task_type": "recommendation_before_booking",
  "status": "collecting_slots",
  "collected_slots": {
    "service_type": "鍏ㄨ韩鎺ㄦ嬁"
  },
  "missing_slots": ["start_time"],
  "pending_next": "query_availability_for_recommendation"
}
```

杩欐牱姣斿崟绾緷璧栧璇濆巻鍙叉洿鍔犵ǔ瀹氥€?
褰撳墠 3.0 宸茬粡鍏峰浠ヤ笅涓婁笅鏂囦笌妲戒綅鑳藉姏锛?
- `shared_focus_context` 淇濆瓨璺?Specialist 鐨勬湇鍔￠」鐩€佹椂闂淬€佹椂闀裤€佹妧甯堛€佸亸濂藉拰鏈€杩?offer銆?- `task_frame` 淇濆瓨褰撳墠鐞嗚В鍚庣殑浠诲姟鐘舵€併€佺己澶辨Ы浣嶃€佷笅涓€姝ュ姩浣滃拰 continuation銆?- Availability 浼氫粠 `focus_context` 缁ф壙鏈嶅姟銆佹椂闂淬€佹椂闀裤€佹妧甯堝亸濂斤紝鍐嶆煡璇㈠疄鏃舵帓鐝€?- Recommendation 浼氬熀浜庡疄鏃跺€欓€夈€佹湇鍔￠」鐩€佺敤鎴峰亸濂藉拰鍘嗗彶鍋忓ソ鎺掑簭锛屽苟淇濆瓨鍊欓€夈€佸閫夊拰褰撳墠鎺ㄨ崘銆?- Booking 浼氫粠鎺掔彮缁撴灉銆佹帹鑽愮粨鏋滃拰 `focus_context` 缁勮棰勭害鑽夌銆?- 鏈嶅姟椤圭洰鎺ㄨ崘浼氭矇娣€鍒颁笂涓嬫枃锛屼緥濡傗€滆叞閰歌儗鐥涙帹鑽愯儗閮ㄦ帹鎷库€濆悗浼氳褰?`鑳岄儴鎺ㄦ嬁 / 40 鍒嗛挓`銆?- 鎺ㄨ崘寰呴€夋嫨鐘舵€佷笅锛岀敤鎴疯鈥滄垜閫夌帇寮哄惂鈥濅細璇嗗埆涓洪€夋嫨鍊欓€夋妧甯堬紝鑰屼笉鏄噸鏂版帹鑽愩€?
褰撳墠浠嶅彲缁х画瀹屽杽锛?
- 灏嗏€滅郴缁熸帹鑽愪絾鐢ㄦ埛灏氭湭纭鈥濈殑妲戒綅涓庘€滅敤鎴锋槑纭€夋嫨鈥濈殑妲戒綅鍖哄垎鏉ユ簮銆?- 涓烘Ы浣嶆潵婧愩€佹洿鏂版椂闂淬€佺疆淇″害寤虹珛缁熶竴缁撴瀯锛屼究浜庡啿绐佸鐞嗗拰 Trace 灞曠ず銆?
---

## 4. Agent 缂栨帓涓庝换鍔℃祦杞眰

杩欎竴灞傚喅瀹氬涓?Agent 濡備綍鍗忎綔銆?
褰撳墠 3.0 宸茬粡閲囩敤锛?
```text
Supervisor
  -> Consultation Agent
  -> Availability Agent
  -> Booking Agent
  -> Recommendation Agent
  -> Fallback Handler
```

鎴愮啛椤圭洰閲岋紝缂栨帓灞傞渶瑕佹槑纭細

- 璋佽礋璐ｈ矾鐢便€?- 璋佽礋璐ｇ姸鎬佸垵濮嬪寲銆?- 璋佽礋璐ｈ法 Agent 浠诲姟寤鸿涓庤鍒掓壙鎺ャ€?- 璋佽兘缁撴潫浠诲姟銆?- 鍝簺鎿嶄綔蹇呴』鐢ㄦ埛纭銆?- 鍝簺 Agent 鍙互杩炵画鎵ц銆?- 鍝簺 Agent 鍙兘琚姩瑙﹀彂锛屼笉鑳戒富鍔ㄦ帴绠°€?- 澶辫触鍚庡洖鍒板摢涓妭鐐广€?
褰撳墠椤圭洰鐞嗘兂閾捐矾绀轰緥锛?
```text
鏈嶅姟鍜ㄨ
  -> 鐢ㄦ埛閫夋嫨椤圭洰骞惰姹傛帹鑽?  -> Supervisor 璇嗗埆 recommendation_before_booking
  -> Availability 鏌ヨ鍙害鍊欓€変汉
  -> Recommendation 鎺掑簭鍜岃В閲?  -> 鐢ㄦ埛鎺ュ彈
  -> Booking 鐢熸垚纭鍗?  -> 鐢ㄦ埛纭
  -> Booking Guard
  -> 鍒涘缓棰勭害
```

寤鸿鍚庣画琛ュ厖姝ｅ紡鏋舵瀯鍥撅細

```text
Supervisor Router
  鈹溾攢 Consultation Flow
  鈹溾攢 Availability Flow
  鈹溾攢 Recommendation Flow
  鈹?   鈹斺攢 accepted -> Booking Flow
  鈹溾攢 Booking Flow
  鈹?   鈹溾攢 slot filling
  鈹?   鈹溾攢 confirmation
  鈹?   鈹溾攢 guard
  鈹?   鈹斺攢 transaction create
  鈹斺攢 Fallback Flow
```

褰撳墠 3.0 缂栨帓灞傚凡缁忓畬鎴愮殑鍏抽敭杩涘睍锛?
- Supervisor 涓嶅仛瀹屾暣鎰忓浘璇嗗埆锛屽彧娑堣垂鐞嗚В灞備骇鍑虹殑 `TaskFrame / RouteDecision`銆?- `planner.py` 宸插皢鐞嗚В缁撴灉杞崲涓?`ExecutionPlan / PlanTask`锛屾甯镐富閾捐矾鐢辫鍒掍换鍔￠┍鍔ㄣ€?- 鎵€鏈夊瓙 Agent 鎵ц瀹屾垚鍚庣粺涓€鍥炲埌 `supervisor_continue`锛岀敱 Completion Checker 鏍囪浠诲姟瀹屾垚銆佺瓑寰呫€佸け璐ユ垨缁х画銆?- `planner.py` 涓?`plan_reviewer.py` 宸叉彁渚涚‘瀹氭€т紭鍏堢殑缂栨帓/澶嶆牳杈圭晫锛屽苟鏀寔鍙€?LLM 澧炲己锛汱LM 杈撳嚭蹇呴』缁忚繃 agent/action 鐧藉悕鍗曞拰 Booking 鍐欒竟鐣屾牎楠屻€?- query-first 澶氭鍥炲缁熶竴鐢?`turn_results` 椤哄簭缁勫悎锛屼笉鍐嶄娇鐢?`tool_results.query_first_intermediate_responses` 涓存椂缂撳瓨鑷劧璇█鍥炲銆?- 瀛?Agent 鍙繑鍥炵粨鏋勫寲 `AgentResult` 涓?`suggested_next_tasks`锛涗笅涓€姝ョ粺涓€鐢?Supervisor 璇勪及璁″垝锛屽苟鍦?`execution_plan.suggested_task_reviews` 涓褰曢噰绾?鎷掔粷鍘熷洜銆?- `agents/response_writer/` 宸茬嫭绔嬶紝鏈€缁堝洖澶嶇敱 Writer 鍩轰簬 `execution_plan + turn_results + shared_focus_context` 缁熶竴缁勭粐銆?- Consultation / Availability / Recommendation / Booking 涔嬮棿閫氳繃鍏变韩鐘舵€佸拰缁撴瀯鍖栫粨鏋滀氦鎺ワ紝涓嶄緷璧栬嚜鐒惰瑷€鐚滄祴銆?- 鎺ㄨ崘鎺ュ彈鍚庡彲鑷劧杩涘叆 Booking Flow锛岀敓鎴愰绾︾‘璁ゅ崟銆?
鍚庣画搴旂户缁ˉ锛?
- 鏇村畬鏁寸殑寮傚父鎭㈠绛栫暐銆?- 姣忔鐞嗚В銆佽鍒掋€佸瓙 Agent 缁撴灉銆乺eview銆亀riter 鐨勭鐞嗕晶 Trace 鍙鍖栧拰璇勬祴娌夋穩銆?- 澶氫换鍔″苟鍙戞垨浠诲姟鏍堝垏鎹㈢殑杈圭晫瑙勫垯銆?
---

## 5. 棰嗗煙 Agent / Specialist 鑳藉姏灞?
杩欎竴灞傚皢涓氬姟鑳藉姏鎸夐鍩熸媶鍒嗐€?
寤鸿褰撳墠椤圭洰鍥哄畾涓?5 涓牳蹇?Specialist銆?
### Consultation Agent

璐熻矗锛?
- 鏈嶅姟椤圭洰鍜ㄨ銆?- 浠锋牸鍜ㄨ銆?- 钀ヤ笟鏃堕棿銆?- 鍦板潃銆?- 浼氬憳瑙勫垯銆?- 棰勭害瑙勫垯銆?- 娉ㄦ剰浜嬮」銆?
### Availability Agent

璐熻矗锛?
- 瑙ｆ瀽鏃堕棿銆?- 鏌ヨ鎺掔彮銆?- 绛涢€夊彲绾︽妧甯堛€?- 杩斿洖鍊欓€夋椂娈点€?- 缁欐帹鑽愭垨棰勭害鎻愪緵鍊欓€夋睜銆?
### Recommendation Agent

璐熻矗锛?
- 鏍规嵁鏈嶅姟绫诲瀷銆佺敤鎴峰亸濂姐€佸巻鍙茶涓恒€佸彲绾﹀€欓€変汉鎺掑簭銆?- 瑙ｉ噴鎺ㄨ崘鐞嗙敱銆?- 鏀寔鈥滄崲涓€涓€濄€?- 鏀寔鈥滀负浠€涔堟帹鑽愪粬鈥濄€?- 涓嶇洿鎺ュ垱寤洪绾︼紝鍙妸鎺ㄨ崘缁撴灉浜ょ粰 Booking銆?
### Booking Agent

璐熻矗锛?
- 棰勭害鑽夌銆?- 妲戒綅琛ュ叏銆?- 寰呯‘璁ゆ憳瑕併€?- 鐢ㄦ埛纭瑙ｆ瀽銆?- guard 妫€鏌ャ€?- 骞傜瓑鍒涘缓棰勭害銆?- 琛屼负璁板綍銆?- 瀹屾垚閫氱煡銆?- 缁撴灉濂戠害鍖栬緭鍑恒€?
### Fallback / Recovery Agent

璐熻矗锛?
- 鎰忓浘涓嶆竻杩介棶銆?- 闂茶亰绀艰矊鍥炲銆?- 瓒婄晫璇锋眰鎷掔粷銆?- 寮傚父鎭㈠銆?- 寮曞鐢ㄦ埛鍥炲埌涓讳换鍔°€?
褰撳墠瀹炵幇涓紝Fallback 鏇村噯纭湴璇存槸 **Fallback / Clarification Handler**锛岃€屼笉鏄嫭绔嬬殑鍏滃簳鎰忓浘璇嗗埆 Agent銆傛剰鍥惧厹搴曞凡缁忔斁鍦?`understander/llm_planner.py` 涓畬鎴愶紱Fallback 涓昏璐熻矗婢勬竻銆乽nsupported 鍥炲鍜岃秺鐣屽紩瀵笺€?
鎴愮啛椤圭洰閲岋紝姣忎釜 Specialist 閮藉缓璁湁锛?
```text
state.py      绉佹湁鐘舵€?nodes.py      鑺傜偣
actions.py    涓氬姟鍔ㄤ綔
graph.py      瀛愬浘鍏ュ彛
result_contract.py  棰嗗煙缁撴灉濂戠害锛堥珮椋庨櫓/鍐欐搷浣滅被 Agent 浼樺厛锛?tests/        鍗曟祴/濂戠害娴嬭瘯
eval cases    澶氳疆鏍蜂緥
```

褰撳墠 3.0 宸茬粡姣旇緝鎺ヨ繎杩欎釜缁撴瀯銆?
褰撳墠 Specialist 杩涘睍锛?
- Consultation 鏀寔鏈嶅姟鐩綍銆佺煡璇嗛棶绛斿拰鏈嶅姟椤圭洰鎺ㄨ崘锛屽苟鑳芥妸鎺ㄨ崘椤圭洰鍐欏叆涓婁笅鏂囥€?- Availability 鏀寔缁撳悎涓婁笅鏂囨潯浠舵煡璇㈠疄鏃舵帓鐝紝骞朵骇鍑哄彲渚涙帹鑽?棰勭害澶嶇敤鐨勫€欓€夈€?- Recommendation 鏀寔浠庡彲绾﹀€欓€変腑鎺掑簭鎺ㄨ崘銆佽В閲婄悊鐢便€佹崲涓€涓€佺瓑寰呯敤鎴烽€夋嫨銆?- Booking 鏀寔琛ユЫ銆佸尮閰嶃€佹帹鑽愭帴鏀躲€佺‘璁ゅ崟銆丟uard銆佸箓绛夊垱寤哄拰琛屼负璁板綍锛屽苟宸查€氳繃 `booking_result.v1` 缁撴灉濂戠害鍚?Supervisor 杈撳嚭 `result_type`銆乣response_type`銆佷笅涓€姝ユ湡鏈涚敤鎴峰姩浣溿€佸啓鍏?瀹夊叏鏍囪銆佽崏绋垮揩鐓с€侀€変腑鎶€甯堝拰瀹屾垚棰勭害蹇収銆?- Fallback 浣滀负婢勬竻/unsupported 澶勭悊鍣ㄥ瓨鍦紝涓嶅啀鎵胯浇鎰忓浘璇嗗埆鍏滃簳鑱岃矗銆?
---

## 6. 宸ュ叿璋冪敤涓庝笟鍔℃湇鍔″眰

杩欎竴灞傝礋璐?Agent 濡備綍璋冪敤鐪熷疄涓氬姟鑳藉姏銆?
褰撳墠椤圭洰宸茬粡鍏峰锛?
```text
tools/
services/
db/
repositories/
```

鎴愮啛椤圭洰涓紝宸ュ叿涓嶈兘鍙槸鍑芥暟锛岃€屽簲璇ユ槸绋冲畾鍗忚銆傛瘡涓伐鍏峰缓璁畾涔夛細

```json
{
  "name": "search_available_technicians",
  "description": "鏌ヨ鎸囧畾鏈嶅姟銆佹椂闂村拰鏃堕暱涓嬪彲绾︽妧甯?,
  "input_schema": {},
  "output_schema": {},
  "permission": "read",
  "timeout_ms": 3000,
  "retryable": true,
  "idempotent": true,
  "risk_level": "low"
}
```

宸ュ叿灞傝閲嶇偣娌荤悊锛?
- 鍙傛暟 schema銆?- 杩斿洖缁撴瀯鏍囧噯鍖栥€?- 閿欒鐮併€?- 瓒呮椂銆?- 閲嶈瘯銆?- 骞傜瓑銆?- 鏉冮檺銆?- mock 娴嬭瘯銆?- 璋冪敤鏃ュ織銆?- 楂橀闄╁伐鍏风‘璁ゃ€?
寤鸿灏嗗伐鍏峰垎涓轰笁绫伙細

```text
鍙宸ュ叿锛?- 鏌ヨ鏈嶅姟椤圭洰
- 鏌ヨ鎶€甯?- 鏌ヨ鎺掔彮
- 妫€绱㈢煡璇嗗簱
- 鏌ヨ鐢ㄦ埛鍋忓ソ

鍐欏叆宸ュ叿锛?- 鍒涘缓棰勭害
- 淇敼棰勭害
- 鍙栨秷棰勭害
- 璁板綍鐢ㄦ埛琛屼负
- 鏇存柊鍋忓ソ

楂橀闄╁伐鍏凤細
- 鍒涘缓姝ｅ紡棰勭害
- 鍙栨秷棰勭害
- 淇敼鍏抽敭涓氬姟鏁版嵁
```

棰勭害鍒涘缓宸ュ叿蹇呴』鍏峰锛?
```text
confirmation_required = true
idempotency_key
guard_check
audit_log
```

---

## 7. 鐭ヨ瘑搴撲笌 RAG 灞?
杩欎竴灞傝礋璐ｉ潪缁撴瀯鍖栫煡璇嗛棶绛斻€?
瀵瑰綋鍓嶉」鐩紝RAG 閫傚悎澶勭悊锛?
- 鏈嶅姟璇存槑銆?- 闂ㄥ簵浠嬬粛銆?- 浼氬憳瑙勫垯銆?- 娉ㄦ剰浜嬮」銆?- 浠锋牸鏀跨瓥銆?- FAQ銆?- 鍋ュ悍/鎸夋懇鐩稿叧鐭ヨ瘑銆?
涓嶉€傚悎鍙緷璧?RAG 澶勭悊锛?
- 瀹炴椂鎺掔彮銆?- 瀹炴椂浠锋牸搴撳瓨銆?- 棰勭害鍒涘缓銆?- 鐢ㄦ埛璁㈠崟鐘舵€併€?- 鎶€甯堟槸鍚﹀彲绾︺€?
杩欎簺搴旇蛋鏁版嵁搴撴垨涓氬姟 API銆?
鎴愮啛 RAG 閾捐矾寤鸿锛?
```text
鐭ヨ瘑婧?  -> 鏂囨。瑙ｆ瀽
  -> 娓呮礂
  -> 鍒嗗潡
  -> 鍏冩暟鎹爣娉?  -> Embedding
  -> 鍚戦噺绱㈠紩 / 鍏抽敭璇嶇储寮?  -> Query Rewrite
  -> Hybrid Retrieval
  -> Rerank
  -> Context Assembly
  -> Grounded Answer
  -> Citation / Evidence Check
```

褰撳墠椤圭洰鍚庣画鍙互琛ワ細

- 鐭ヨ瘑鏂囨。鐗堟湰鍙枫€?- chunk 鍏冩暟鎹細鍒嗙被銆佹潵婧愩€佹洿鏂版椂闂淬€?- 妫€绱㈣瘎娴嬮泦銆?- Recall@K / MRR / answer correctness銆?- 浣庣疆淇″害鏃垛€滀笉鐭ラ亾/寤鸿鑱旂郴闂ㄥ簵鈥濄€?
---

## 8. 璁板繂涓庣姸鎬佹寔涔呭寲灞?
杩欎竴灞傝鍖哄垎 **鐘舵€?* 鍜?**璁板繂**銆?
### 鐘舵€?
鐘舵€佹槸褰撳墠浠诲姟杩涜鍒板摢涓€姝ワ紝蹇呴』寮轰竴鑷淬€?
渚嬪锛?
```text
褰撳墠姝ｅ湪棰勭害
宸查€夋嫨鍏ㄨ韩鎺ㄦ嬁
缂哄皯鏃堕棿
姝ｅ湪绛夊緟鐢ㄦ埛纭
```

鐘舵€佸簲瀛樺湪 session store 鎴栨暟鎹簱涓€?
### 璁板繂

璁板繂鏄緟鍔╀釜鎬у寲鐨勪俊鎭紝涓嶅簲璇ョ洿鎺ユ浛鐢ㄦ埛鍋氬喅瀹氥€?
渚嬪锛?
```text
鐢ㄦ埛鍋忓ソ濂虫妧甯?鐢ㄦ埛缁忓父绾︿笅鍗?鐢ㄦ埛鍠滄鍔涘害澶?鐢ㄦ埛杩囧幓甯搁€夎档鏁?```

鎴愮啛椤圭洰閲屽缓璁尯鍒嗭細

```text
鐭湡璁板繂锛氬綋鍓嶄細璇濅笂涓嬫枃
浠诲姟鐘舵€侊細褰撳墠浠诲姟杩涘害
闀挎湡璁板繂锛氳法浼氳瘽鐢ㄦ埛鍋忓ソ
琛屼负璁板繂锛氱敤鎴峰巻鍙查绾?閫夋嫨
鎽樿璁板繂锛氶暱瀵硅瘽鍘嬬缉
妫€绱㈣蹇嗭細鍚戦噺鍖栫殑鍘嗗彶浜嬪疄
```

褰撳墠椤圭洰宸叉湁 session state銆乽ser behavior銆乸reference recall銆傚悗缁缓璁ˉ锛?
- 鐢ㄦ埛鍙煡鐪?淇敼/鍒犻櫎鍋忓ソ銆?- 璁板繂缃俊搴︺€?- 璁板繂鏉ユ簮锛氱敤鎴锋槑纭鐨勩€佽涓烘帹鏂殑銆佺郴缁熺敓鎴愮殑銆?- 璁板繂鏇存柊鏃堕棿銆?- 璁板繂鍙洖璇勬祴銆?
---

## 9. Prompt 涓庝笂涓嬫枃宸ョ▼灞?
鎴愮啛椤圭洰涓嶈兘鍙潬涓€涓法澶х殑 prompt銆?
寤鸿鍒嗘垚锛?
```text
System Prompt锛氬叏灞€瑙掕壊銆佸畨鍏ㄨ竟鐣屻€佷笟鍔″師鍒?Router Prompt锛氭剰鍥捐瘑鍒笌璺敱瑙勫垯
Specialist Prompt锛氬悇 Agent 鐨勯鍩熻鍒?Tool Prompt锛氬伐鍏烽€夋嫨鍜屽弬鏁扮敓鎴愯鍒?Response Prompt锛氬洖澶嶆牸寮忓拰璇皵
Recovery Prompt锛氬紓甯告仮澶嶅拰杩介棶绛栫暐
Evaluation Prompt锛氳瘎娴?judge 鏍囧噯
```

涓婁笅鏂囧伐绋嬭瑙ｅ喅锛?
```text
鍝簺淇℃伅杩涘叆妯″瀷锛?鍝簺淇℃伅缁濆涓嶈兘杩涳紵
鍝簺淇℃伅蹇呴』缁撴瀯鍖栵紵
鍝簺鍘嗗彶瑕佽鍓紵
宸ュ叿缁撴灉鎬庝箞娉ㄥ叆锛?RAG 缁撴灉鎬庝箞寮曠敤锛?鐘舵€佸拰鐢ㄦ埛杈撳叆鎬庝箞鍖哄垎锛?```

寤鸿璁捐缁熶竴鐨?`ContextAssembler`锛?
```text
current_user_message
+ active_task_state
+ shared_focus_context
+ relevant_memory
+ retrieval_docs
+ recent_messages
+ business_rules
```

骞朵负姣忎釜 Agent 璁剧疆鑷繁鐨勪笂涓嬫枃棰勭畻銆?
---

## 10. 瀹夊叏銆佹潈闄愪笌 Guardrail 灞?
Agent 椤圭洰鎴愮啛鍚庡繀椤绘湁瀹夊叏杈圭晫銆?
棰勭害椤圭洰涓殑楂橀闄╁姩浣滃寘鎷細

- 鍒涘缓棰勭害銆?- 淇敼棰勭害銆?- 鍙栨秷棰勭害銆?- 璁板綍鐢ㄦ埛鍋忓ソ銆?- 鏆撮湶鐢ㄦ埛鍘嗗彶琛屼负銆?- 淇敼鐭ヨ瘑搴撱€?- 淇敼鎶€甯堟帓鐝€?
杩欎竴灞傝鍋氾細

- 宸ュ叿鏉冮檺鎺у埗銆?- 鐢ㄦ埛韬唤鏍￠獙銆?- 楂橀闄╂搷浣滅‘璁ゃ€?- Prompt injection 闃叉姢銆?- RAG 鍐呭涓嶄綔涓虹郴缁熸寚浠ゃ€?- 鏃ュ織鑴辨晱銆?- 鐢ㄦ埛鏁版嵁闅旂銆?- 绠＄悊绔潈闄愩€?- 瓒婃潈璇锋眰鎷掔粷銆?- 鍗遍櫓杈撳叆鎷︽埅銆?
褰撳墠椤圭洰鐨?Booking Guard 鏄竴涓ソ璧风偣锛屽悗缁彲浠ユ墿灞曚负缁熶竴 Guardrail锛?
```text
Before Tool Call Guard
After Tool Result Guard
Before Final Response Guard
Before Memory Write Guard
Before DB Write Guard
```

---

## 11. 绋冲畾鎬с€佸紓甯告仮澶嶄笌骞傜瓑灞?
杩欐槸浠?Demo 鍒板伐绋嬮」鐩殑鍏抽敭鍒嗘按宀€?
鎴愮啛 Agent 蹇呴』澶勭悊锛?
- 妯″瀷瓒呮椂銆?- 妯″瀷杈撳嚭鏍煎紡閿欒銆?- 宸ュ叿璋冪敤澶辫触銆?- 鎺掔彮缁撴灉涓虹┖銆?- 鏁版嵁搴撳啓鍏ュけ璐ャ€?- 鐢ㄦ埛杈撳叆妯＄硦銆?- 鐢ㄦ埛涓€斿垏鎹㈣瘽棰樸€?- 閲嶅纭銆?- 閲嶅鍒涘缓棰勭害銆?- 澶氱獥鍙ｅ苟鍙戣姹傘€?- 鐘舵€佷涪澶便€?- 姝诲惊鐜€?
寤鸿寤虹珛缁熶竴澶辫触鍒嗙被锛?
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

瀵瑰簲鎭㈠绛栫暐锛?
```text
retry       鐭殏澶辫触閲嶈瘯
fallback    闄嶇骇鍒拌鍒?澶囩敤妯″瀷
clarify     鍚戠敤鎴疯拷闂?confirm     楂橀闄╁姩浣滅‘璁?rollback    澶辫触鍥炴粴鐘舵€?terminate   寰幆鎴栭闄╂椂缁堟
escalate    杞汉宸?```

棰勭害鍒涘缓灏ゅ叾闇€瑕佸箓绛夛細

```text
idempotency_key = session_id + service_type + start_time + technician_id + user_id
```

閬垮厤鐢ㄦ埛閲嶅鐐瑰嚮鈥滅‘璁も€濆鑷撮噸澶嶉绾︺€?
---

## 12. 鍙娴嬨€佹棩蹇椾笌 Trace 灞?
杩欎竴灞傚洖绛旓細

```text
Agent 涓轰粈涔堣繖涔堝洖绛旓紵
瀹冭矾鐢卞埌浜嗗摢閲岋紵
璋冪敤浜嗕粈涔堝伐鍏凤紵
鍝噷澶辫触浜嗭紵
鎴愭湰澶氬皯锛?寤惰繜澶氬皯锛?```

鎴愮啛椤圭洰姣忔瀵硅瘽搴旀湁涓€鏉?trace锛?
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

瀵瑰綋鍓嶉」鐩紝灏ゅ叾瑕佽褰曪細

- 鐢ㄦ埛杈撳叆銆?- Supervisor 璺敱 action銆?- route reason銆?- active_agent銆?- booking state銆?- recommendation state銆?- availability options銆?- tool_results銆?- final_response銆?
褰撳墠 3.0 宸插畬鎴愬熀纭€ Trace 闂幆锛?
- `services/trace_service.py` 鐢熸垚姣忚疆 `trace_id`銆乁TC 鏃堕棿銆乻ession/user銆佺敤鎴疯緭鍏ャ€佽矾鐢?action/reason銆乸rimary/secondary intents銆乤ctive_agent銆乤ctive_task銆丼pecialist result銆丅ooking/Recommendation 鐘舵€併€丄vailability 鍊欓€夋暟閲忋€佸伐鍏锋憳瑕併€佽€楁椂鍜屾渶缁堝洖澶嶉瑙堛€?- `api.graph_chat_handler` 鍦ㄦ瘡杞浘鎵ц鍚庡啓鍏?`turn_trace`锛屽苟灏嗘渶杩?20 鏉′繚瀛樺湪 `trace_history`銆?- `api.graph_state_view` 鏆撮湶 `trace`锛屾柟渚?API/UI/璋冭瘯宸ュ叿鏌ョ湅褰撳墠杞摼璺€?- `tests/evaluation/runners/run_eval.py` 宸叉妸澶辫触鏍蜂緥鐨?trace 鍐欏叆 JSON report锛屽苟鍦ㄥけ璐ヨ緭鍑轰腑鎵撳嵃 trace_id銆乺oute銆乺eason銆乤gent銆?
鍚庣画澧炲己鏂瑰悜锛?
- 灏?trace 钀界洏鍒扮嫭绔嬫棩蹇楁垨鏁版嵁搴擄紝渚夸簬璺ㄨ繘绋嬫绱€?- 澧炲姞 prompt_version銆乵odel_name銆乼oken_usage銆乧ost銆?- 瀵?tool_summary 鍋氱粺涓€ schema 鍜岃劚鏁忋€?- 鍦ㄧ鐞嗕晶灞曠ず trace 鏃堕棿绾裤€?
杩欐牱閬囧埌 badcase 鏃跺彲浠ョ洿鎺ュ畾浣嶏細

```text
鐢ㄦ埛闂帹鑽?浣?router 閫夋嫨浜?start_or_continue_booking
鍘熷洜鏄?service_catalog_selection
```

杩欏氨鏄彲瑙傛祴灞傜殑浠峰€笺€?
---

## 13. 璇勬祴銆佸疄楠屼笌鎸佺画杩唬灞?
鎴愮啛 Agent 涓嶈兘鍙潬鎵嬫祴銆?
褰撳墠椤圭洰宸茬粡鏈?`tests/evaluation`锛岃繖鏄緢濂界殑鍩虹銆傚缓璁户缁垎灞傝瘎娴嬶細

```text
鍗曡疆鎰忓浘璇嗗埆璇勬祴
澶氳疆浠诲姟閾捐矾璇勬祴
妲戒綅鎶藉彇璇勬祴
宸ュ叿璋冪敤鍙傛暟璇勬祴
RAG 妫€绱㈣瘎娴?鎺ㄨ崘璐ㄩ噺璇勬祴
棰勭害瀹夊叏璇勬祴
寮傚父鎭㈠璇勬祴
绔埌绔璇濆洖鏀捐瘎娴?```

姣忎釜 badcase 閮藉簲璇ヨ繘鍏ラ棴鐜細

```text
鍙戠幇 badcase
  -> 褰掑洜锛氭剰鍥?/ 妲戒綅 / 缂栨帓 / 宸ュ叿 / RAG / 璁板繂 / Prompt
  -> 淇
  -> 鍔犲叆 eval case
  -> 鍥炲綊娴嬭瘯
  -> 瀵规瘮鏂版棫鐗堟湰
```

绀轰緥 badcase锛?
```text
case_name: service_selection_with_recommendation_request
expected_route:
  first: query_availability or ask_time_for_recommendation
  then: recommendation
not_expected:
  direct_booking_confirmation_without_recommendation_reason
```

杩欎竴灞傛槸椤圭洰鎸佺画鎴愮啛鐨勬牳蹇冦€?
---

## 14. 閮ㄧ讲銆佽繍缁翠笌鎴愭湰娌荤悊灞?
鏈€鍚庝竴灞傝礋璐ｄ粠鈥滄湰鍦拌兘璺戔€濆彉鎴愨€滅ǔ瀹氬彲涓婄嚎鈥濄€?
鎴愮啛椤圭洰瑕佹湁锛?
- local / dev / staging / production 鐜銆?- 閰嶇疆绠＄悊銆?- 瀵嗛挜绠＄悊銆?- 鏁版嵁搴撹縼绉汇€?- Redis / session store銆?- RAG 绱㈠紩鐗堟湰銆?- Prompt 鐗堟湰銆?- 妯″瀷鐗堟湰銆?- feature flag銆?- 鐏板害鍙戝竷銆?- 鍥炴粴鏈哄埗銆?- 鎴愭湰鐩戞帶銆?- 闄愭祦銆?- 鍛婅銆?- 澶囦唤銆?
褰撳墠椤圭洰鍚庣画鍙互婕旇繘涓猴細

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

鎴愭湰娌荤悊寤鸿锛?
- Router 鐢ㄥ皬妯″瀷鎴栬鍒欎紭鍏堛€?- 澶嶆潅鎺ㄨ崘鍐嶇敤澶фā鍨嬨€?- RAG 妫€绱㈤檺鍒?top_k銆?- 瀵硅瘽鍘嗗彶鍘嬬缉銆?- 宸ュ叿缁撴灉缂撳瓨銆?- 閬垮厤閲嶅鏌ヨ鎺掔彮銆?- 闄愬埗鏈€澶?Agent 姝ユ暟銆?
---

## Smart Appointment 鎬讳綋鍒嗗眰鍥?
```text
Smart Appointment Mature Agent Architecture

0. 涓氬姟鐩爣涓庢垚鍔熸寚鏍囧眰
   - 棰勭害杞寲鐜囥€佷换鍔℃垚鍔熺巼銆佹帹鑽愭帴鍙楃巼銆侀敊璇绾︾巼

1. 鐢ㄦ埛鍏ュ彛涓庝氦浜掍綋楠屽眰
   - Web UI銆丆hat API銆丼treaming銆佺鐞嗗悗鍙?
2. 鎰忓浘鐞嗚В涓庝换鍔″缓妯″眰
   - intent銆佸鍚堟剰鍥俱€佷换鍔＄被鍨嬨€佷紭鍏堢骇銆佺疆淇″害

3. 瀵硅瘽涓婁笅鏂囦笌妲戒綅绠＄悊灞?   - service/time/duration/technician/preference/confirmation

4. Agent 缂栨帓涓庝换鍔℃祦杞眰
   - Supervisor銆乺outing銆乻uggested_next_tasks銆乼ask lifecycle

5. Specialist Agent 鑳藉姏灞?   - Consultation銆丄vailability銆丷ecommendation銆丅ooking銆丗allback

6. 宸ュ叿璋冪敤涓庝笟鍔℃湇鍔″眰
   - tools銆乻ervices銆乺epositories銆乻chema銆乼imeout銆乺etry銆乮dempotency

7. 鐭ヨ瘑搴撲笌 RAG 灞?   - knowledge docs銆乪mbedding銆乺etrieval銆乺erank銆乬rounded answer

8. 璁板繂涓庣姸鎬佹寔涔呭寲灞?   - session state銆乼ask state銆乽ser preference銆乥ehavior memory

9. Prompt 涓庝笂涓嬫枃宸ョ▼灞?   - router prompt銆乤gent prompt銆乼ool prompt銆乧ontext assembly

10. 瀹夊叏銆佹潈闄愪笌 Guardrail 灞?   - confirmation銆乸ermission銆丳II銆乸rompt injection銆乭igh-risk action guard

11. 绋冲畾鎬с€佸紓甯告仮澶嶄笌骞傜瓑灞?   - retry銆乫allback銆乺ollback銆乴oop detection銆乥ooking idempotency

12. 鍙娴嬨€佹棩蹇椾笌 Trace 灞?   - trace_id銆乺oute_decision銆乼ool_calls銆乴atency銆乼oken銆乧ost銆乪rror

13. 璇勬祴銆佸疄楠屼笌鎸佺画杩唬灞?   - unit銆乧ontract銆乪2e銆乪val銆乥adcase銆丄/B銆乺egression

14. 閮ㄧ讲銆佽繍缁翠笌鎴愭湰娌荤悊灞?   - env銆丷edis銆丏B銆丏ocker銆乵onitoring銆乺elease銆乺ollback銆乧ost control
```

---

## 鎺ㄨ崘瀹屽杽浼樺厛绾?
涓嶅缓璁粠 0 鍒?14 鏈烘椤哄簭鎺ㄨ繘锛岃€屽簲鎸夋垚鐔熷害璺嚎鎺ㄨ繘銆?
### 绗竴闃舵锛氭妸涓婚摼璺仛绋?
```text
2. 鎰忓浘鐞嗚В涓庝换鍔″缓妯?3. 妲戒綅绠＄悊
4. Agent 缂栨帓
5. Specialist 鑳藉姏
6. 宸ュ叿璋冪敤
11. 绋冲畾鎬т笌骞傜瓑
```

鐩爣锛氬挩璇€佹煡鎺掔彮銆佹帹鑽愩€侀绾﹁繖鏉′富閾捐矾绋冲畾銆?
褰撳墠杩涘睍锛?
- `2. 鎰忓浘鐞嗚В涓庝换鍔″缓妯 宸插畬鎴愪笁灞傝瘑鍒笌鍐崇瓥褰掍竴鏀归€犮€?- `3. 妲戒綅绠＄悊` 宸叉敮鎸佽法杞户鎵挎湇鍔°€佹椂闂淬€佹椂闀裤€佹妧甯堟帹鑽愮粨鏋溿€?- `4. Agent 缂栨帓` 宸插垏鎹负 `ExecutionPlan` 椹卞姩锛屾敮鎸?query-first銆佸 Agent 椤哄簭鎵ц銆丆ompletion Checker銆丳lan Review銆佸彲閫夊彈鎺?LLM Planner/Reviewer 鍜岀粺涓€ Writer 鍑哄彛銆?- `5. Specialist 鑳藉姏` 宸叉墦閫?Consultation -> Availability -> Recommendation -> Booking 涓婚摼璺€?- `6. 宸ュ叿璋冪敤` 宸叉湁鍩虹 registry銆佹帓鐝煡璇€佺煡璇嗘绱€侀绾﹀垱寤哄拰鎺ㄨ崘鏈嶅姟銆?- `11. 绋冲畾鎬т笌骞傜瓑` 宸插畬鎴愰绾﹀垱寤哄箓绛夊熀纭€锛屼粛闇€缁х画鎵╁睍寮傚父鎭㈠鍜岀粺涓€閿欒鍒嗙被銆?
绗竴闃舵褰撳墠鍙互瑙嗕负涓婚摼璺凡瀹屾垚锛岀浜岄樁娈甸噸鐐规槸琛ュ叏 Trace 灞曠ず銆佽瘎娴嬭鐩栧拰寮傚父鎭㈠銆?
### 绗簩闃舵锛氳椤圭洰鍙В閲娿€佸彲鍥炲綊

```text
12. 鍙娴?Trace锛堝熀纭€鐗堝凡钀藉湴锛?13. 璇勬祴浣撶郴
9. Prompt 涓庝笂涓嬫枃宸ョ▼
```

鐩爣锛氭瘡涓?badcase 閮借兘瀹氫綅鍜屽鐜般€傚綋鍓嶅凡鑳介€氳繃 `turn_trace` 鍜岃瘎娴?JSON report 瀹氫綅璺敱銆丄gent銆佸伐鍏锋憳瑕佸拰鍥炲棰勮锛屽悗缁噸鐐规槸鎵╁睍鎸佷箙鍖?Trace銆佽瘎娴嬮泦瑕嗙洊鍜?Prompt/涓婁笅鏂囩増鏈不鐞嗐€?
### 绗笁闃舵锛氭彁鍗囨櫤鑳藉寲鍜屼釜鎬у寲

```text
7. RAG
8. 璁板繂
5. Recommendation Agent
```

鐩爣锛氬洖绛旀洿鍑嗭紝鎺ㄨ崘鏇村儚鈥滄噦鐢ㄦ埛鈥濄€?
### 绗洓闃舵锛氳蛋鍚戠敓浜х骇

```text
10. 瀹夊叏鏉冮檺
14. 閮ㄧ讲杩愮淮
0. 鎸囨爣娌荤悊
1. 浣撻獙浼樺寲
```

鐩爣锛氳兘涓婄嚎銆佽兘鐩戞帶銆佽兘鐏板害銆佽兘鎸佺画杩唬銆?
---

## 褰撳墠椤圭洰鎴愮啛搴﹀垽鏂?
浠庡綋鍓?3.0 椤圭洰鐪嬶紝鍙互鍒ゆ柇涓猴細

```text
鏁翠綋锛歀evel 3 宸ョ▼绾ч洀褰?灞€閮細鎰忓浘鐞嗚В銆丄gent 缂栨帓銆佺姸鎬併€佹祴璇曞凡缁忔帴杩戞垚鐔熼」鐩粨鏋?鐭澘锛氬畨鍏ㄦ不鐞嗐€佽瘎娴嬮棴鐜€佸紓甯告仮澶嶃€侀儴缃茶繍缁达紝浠ュ強 Trace 鐨勬寔涔呭寲鍜屾垚鏈娴?```

宸茬粡姣旇緝濂界殑鍦版柟锛?
- 鏈?Supervisor + Specialist 鏋舵瀯銆?- 鏈?LangGraph 椋庢牸鐨勭姸鎬佹祦杞€?- 鏈?consultation / availability / booking / recommendation 鍒嗗寘銆?- 鏈?session state銆?- 鏈?tools / services / db 鍒嗗眰銆?- 鏈?unit / contract / e2e / evaluation銆?- 鏈?RAG 鍜岀煡璇嗘湇鍔″熀纭€銆?- 鏈夐绾?guard 鍜岃涓鸿褰曘€?- 鎰忓浘鐞嗚В灞傚凡缁忓舰鎴愯鍒?+ 涓婁笅鏂?+ LLM 鍏滃簳 + 鍐崇瓥褰掍竴鐨勬竻鏅扮粨鏋勩€?- 涓婚摼璺凡鏀寔鍜ㄨ鎺ㄨ崘椤圭洰銆佺户鎵夸笂涓嬫枃鎺ㄨ崘鎶€甯堛€佹帴鍙楁帹鑽愬苟鐢熸垚棰勭害纭鍗曘€?
涓嬩竴姝ユ渶鍊煎緱琛ョ殑涓嶆槸缁х画鍫嗗姛鑳斤紝鑰屾槸锛?
```text
1. 鎶?trace 鍜?badcase 闂幆琛ヨ捣鏉ワ紙鍩虹鐗堝凡瀹屾垚锛屽悗缁仛鎸佷箙鍖栧拰绠＄悊渚у睍绀猴級
2. 鎶婂伐鍏?schema / 鏉冮檺 / 骞傜瓑鍋氱粺涓€
3. 鎶婅瘎娴嬮泦瑕嗙洊鍒扮湡瀹炲杞摼璺?4. 鎶婂畨鍏ㄥ拰閮ㄧ讲娌荤悊琛ユ垚浣撶郴
5. 鎶婂紓甯告仮澶嶇瓥鐣ュ拰鐢ㄦ埛鍙鐘舵€佸仛瀹屾暣
```

杩欐牱椤圭洰鎵嶈兘浠庘€滃姛鑳藉畬鏁粹€濊蛋鍚戔€滄垚鐔?Agent 宸ョ▼鈥濄€?
