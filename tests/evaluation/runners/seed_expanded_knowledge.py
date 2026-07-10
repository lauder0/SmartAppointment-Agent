"""Seed expanded text knowledge for retrieval and consultation evaluation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


EXPANDED_KNOWLEDGE = [
    {
        "category": "服务介绍",
        "content": "背部推拿主要针对背部肌肉紧张、久坐劳损、姿势不良导致的酸胀不适，服务时长40分钟，价格90元。服务重点是放松脊柱两侧肌肉和背阔肌区域。",
        "keywords": ["背部推拿", "背部按摩", "背痛", "久坐", "90元", "40分钟"],
    },
    {
        "category": "服务介绍",
        "content": "肩颈推拿适合长期低头、伏案办公、肩颈僵硬和轻度酸胀的人群，服务时长30分钟，价格80元。若疼痛剧烈或伴随麻木，建议先就医评估。",
        "keywords": ["肩颈推拿", "低头", "伏案", "肩颈僵硬", "80元", "30分钟"],
    },
    {
        "category": "服务介绍",
        "content": "全身推拿适合想整体放松、缓解疲劳、改善肌肉紧张的人群，服务时长60分钟，价格120元。首次到店或不确定选择什么项目时，可优先考虑全身推拿。",
        "keywords": ["全身推拿", "整体放松", "疲劳", "首次到店", "120元", "60分钟"],
    },
    {
        "category": "服务介绍",
        "content": "足底按摩适合久站、脚部疲劳、睡眠质量较差或想舒缓放松的人群，服务时长45分钟，价格100元。足部皮肤破损或急性炎症时不建议进行。",
        "keywords": ["足底按摩", "脚部疲劳", "睡眠", "足疗", "100元", "45分钟"],
    },
    {
        "category": "服务流程",
        "content": "到店流程为：提前预约或现场咨询，到店后核对预约信息，选择服务项目和技师偏好，技师沟通重点放松部位，完成服务后可反馈体验。",
        "keywords": ["到店流程", "预约流程", "核对预约", "沟通", "反馈"],
    },
    {
        "category": "预约政策",
        "content": "建议至少提前1天预约热门时段。当天预约也可以查询实时排班，但热门技师和晚间时段可能较快约满。",
        "keywords": ["提前预约", "当天预约", "热门时段", "实时排班", "约满"],
    },
    {
        "category": "预约政策",
        "content": "迟到15分钟以内一般可继续服务，但结束时间可能不顺延；迟到超过15分钟建议联系门店重新确认安排，避免影响后续预约。",
        "keywords": ["迟到", "顺延", "超过15分钟", "重新确认", "后续预约"],
    },
    {
        "category": "健康注意事项",
        "content": "孕期、严重心脑血管疾病、急性扭伤、发热、皮肤破损、骨折恢复期等情况不建议直接进行推拿。相关内容仅作服务说明，不能替代医疗诊断。",
        "keywords": ["禁忌", "孕妇", "心脑血管", "皮肤破损", "骨折", "医疗诊断"],
    },
    {
        "category": "健康注意事项",
        "content": "推拿后建议适量饮水，短时间内避免剧烈运动、饮酒和受凉。如果服务后出现明显不适，应及时休息并咨询专业医生。",
        "keywords": ["推拿后", "饮水", "剧烈运动", "饮酒", "受凉", "不适"],
    },
    {
        "category": "技师信息",
        "content": "如果偏好力气大、重手法或深层放松，可以优先选择张伟、王强、郑斌等擅长深层组织按摩和肌肉放松的技师。",
        "keywords": ["力气大", "重手法", "深层放松", "张伟", "王强", "郑斌"],
    },
    {
        "category": "技师信息",
        "content": "如果偏好轻柔、舒缓、助眠或压力放松，可以优先选择李娜、孙丽、吴婷等手法细腻、舒缓放松风格的技师。",
        "keywords": ["轻柔", "舒缓", "助眠", "李娜", "孙丽", "吴婷"],
    },
    {
        "category": "技师信息",
        "content": "可以指定技师预约。如果指定技师在目标时间不可约，系统会根据性别、服务项目和手法偏好推荐可替代技师。",
        "keywords": ["指定技师", "不可约", "替代技师", "推荐", "偏好"],
    },
    {
        "category": "门店地址",
        "content": "门店附近有商场地下停车场，停车费用以现场公示为准。若乘坐地铁，从地铁2号线A口出站后向北步行约100米即可到达。",
        "keywords": ["停车", "地下停车场", "地铁", "A口", "步行100米"],
    },
    {
        "category": "支付发票",
        "content": "门店支持现金、微信、支付宝等常见支付方式。如需发票，请在消费后联系前台登记开票信息。",
        "keywords": ["支付", "现金", "微信", "支付宝", "发票", "开票"],
    },
    {
        "category": "会员服务",
        "content": "会员优惠通常不可与特殊活动重复叠加，具体以门店当日活动规则为准。会员可享受预约优先权和生日当月专属优惠。",
        "keywords": ["会员", "优惠叠加", "活动", "预约优先", "生日优惠"],
    },
    {
        "category": "服务选择建议",
        "content": "如果是第一次到店且主要想放松，推荐全身推拿；如果是肩颈僵硬，推荐肩颈推拿；如果是背部紧张，推荐背部推拿；如果是脚部疲劳或睡眠差，可考虑足底按摩。",
        "keywords": ["第一次", "推荐项目", "肩颈僵硬", "背部紧张", "脚部疲劳", "睡眠差"],
    },
    {
        "category": "服务质量",
        "content": "服务过程中可以随时告诉技师力度偏好，例如轻一点、重点、避开某个部位或重点放松某个区域，技师会根据反馈调整手法。",
        "keywords": ["力度", "轻一点", "重点", "避开部位", "反馈", "调整手法"],
    },
    {
        "category": "预约政策",
        "content": "如需更改预约时间、服务项目或技师偏好，请尽量提前2小时联系门店或在预约确认前直接告诉智能助手修改。",
        "keywords": ["更改预约", "改时间", "换项目", "换技师", "提前2小时"],
    },
]


async def main() -> int:
    from services.knowledge_service import KnowledgeService

    service = KnowledgeService()
    await service.initialize()
    existing_docs = service.get_all_documents()
    existing_keys = {(doc.get("category"), doc.get("content")) for doc in existing_docs}

    added = 0
    skipped = 0
    for item in EXPANDED_KNOWLEDGE:
        key = (item["category"], item["content"])
        if key in existing_keys:
            skipped += 1
            continue
        success = await service.add_document(
            content=item["content"],
            category=item["category"],
            keywords=item["keywords"],
        )
        if success:
            added += 1
        else:
            raise RuntimeError(f"Failed to add knowledge: {item['category']} {item['content'][:30]}")

    print(f"Knowledge seed complete: added={added}, skipped={skipped}, total={service.get_documents_count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
