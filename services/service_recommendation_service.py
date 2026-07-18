"""Service-item recommendation based on user needs and the service catalog."""

from __future__ import annotations

from typing import Any, Dict, List

from services.service_catalog_service import ServiceCatalogService


SERVICE_NEED_KEYWORDS = {
    "背部推拿": ("腰", "背", "腰酸", "腰痛", "背痛", "腰背", "脊柱", "久坐", "劳损"),
    "肩颈推拿": ("肩", "颈", "脖子", "肩颈", "颈椎", "伏案", "电脑", "僵硬"),
    "足底按摩": ("脚", "足", "足底", "睡眠", "助眠", "失眠", "代谢", "疲劳"),
    "全身推拿": ("全身", "疲劳", "疲惫", "乏力", "放松", "累", "乏", "气血", "压力", "舒缓"),
}


class ServiceRecommendationService:
    """Rank catalog service items for a user's expressed need."""

    def __init__(self):
        self.catalog = ServiceCatalogService()

    def recommend(self, user_text: str, focus_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        services = self._services()
        focus_context = focus_context or {}
        text = " ".join(
            str(value)
            for value in (
                user_text,
                focus_context.get("symptom_or_need"),
                focus_context.get("preference"),
            )
            if value
        )
        ranked = sorted(
            (self._score_service(service, text) for service in services),
            key=lambda item: item["score"],
            reverse=True,
        )
        selected = ranked[0] if ranked else {}
        alternatives = ranked[1:3]
        return {
            "success": bool(selected),
            "selected": selected,
            "alternatives": alternatives,
            "input_text": user_text,
        }

    def _services(self) -> List[Dict[str, Any]]:
        try:
            services = self.catalog.get_all_services()
        except Exception:
            services = self.catalog.default_services
        return [dict(service) for service in services or self.catalog.default_services]

    def _score_service(self, service: Dict[str, Any], text: str) -> Dict[str, Any]:
        name = str(service.get("name") or "")
        keywords = SERVICE_NEED_KEYWORDS.get(name, ())
        raw_matched = [keyword for keyword in keywords if keyword and keyword in text]
        matched = [
            keyword
            for keyword in raw_matched
            if not any(keyword != other and keyword in other for other in raw_matched)
        ]
        score = 0.2 + len(matched) * 0.25
        if name and name in text:
            score += 0.7
            matched.insert(0, name)
        return {
            **service,
            "score": round(min(score, 1.0), 4),
            "matched_keywords": list(dict.fromkeys(matched)),
            "price_yuan": _price_yuan(service),
        }


def _price_yuan(service: Dict[str, Any]) -> int | None:
    value = service.get("price_cents")
    try:
        return int(value) // 100
    except Exception:
        return None
