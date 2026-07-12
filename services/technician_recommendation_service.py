"""Explainable technician ranking over a verified availability candidate set."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from services.appointment_service import AppointmentService


PREFERENCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "strong": {
        "label": "力度偏大",
        "aliases": ("力气大", "手劲大", "重一点", "重手法", "按得深", "按透", "力度大", "深层"),
        "positive_terms": ("力气大", "重手法", "深层", "手法扎实", "肌肉放松", "运动损伤"),
        "negative_terms": ("手法细腻", "舒缓", "轻柔", "美容", "淋巴引流"),
    },
    "gentle": {
        "label": "轻柔舒缓",
        "aliases": ("轻一点", "温柔一点", "手法轻", "舒缓", "放松一点", "不要太重"),
        "positive_terms": ("手法细腻", "舒缓", "轻柔", "助眠", "精油", "放松"),
        "negative_terms": ("力气大", "重手法", "深层组织", "手法扎实"),
    },
    "deep_relaxation": {
        "label": "深层放松",
        "aliases": ("深层放松", "肌肉紧", "肌肉酸", "运动后", "健身后", "按透"),
        "positive_terms": ("深层组织", "肌肉放松", "运动损伤", "拉伸", "经络推拿"),
        "negative_terms": ("面部护理", "美容"),
    },
    "sleep_relaxation": {
        "label": "助眠放松",
        "aliases": ("助眠", "睡不好", "压力大", "放松情绪", "失眠"),
        "positive_terms": ("助眠", "舒缓情绪", "压力大", "睡眠差", "头部按摩", "精油"),
        "negative_terms": ("重手法", "运动损伤"),
    },
}


SERVICE_TERMS: Dict[str, tuple[str, ...]] = {
    "全身推拿": ("全身", "深层", "肌肉", "经络", "泰式", "拉伸", "放松"),
    "肩颈推拿": ("肩颈", "颈椎", "肩", "腰背", "深层组织", "中医推拿"),
    "足底按摩": ("足疗", "足底", "助眠"),
    "背部推拿": ("腰背", "腰椎", "背部", "肌肉", "深层组织"),
}


def parse_recommendation_preference(text: str, fallback: str | None = None) -> Dict[str, Any]:
    """Extract a compact, auditable preference profile from natural language."""
    source = " ".join(part for part in (text, fallback or "") if part).strip()
    normalized = re.sub(r"\s+", "", source.lower())
    matched_profiles = []
    for key, profile in PREFERENCE_PROFILES.items():
        if any(alias in normalized for alias in profile["aliases"]):
            matched_profiles.append(key)

    primary = matched_profiles[0] if matched_profiles else None
    return {
        "raw_text": source or None,
        "profile": primary,
        "profile_label": PREFERENCE_PROFILES.get(primary, {}).get("label"),
        "matched_profiles": matched_profiles,
    }


class TechnicianRecommendationService:
    """Rank only technicians already verified as available."""

    def __init__(self, appointment_service: AppointmentService | None = None):
        self.appointment_service = appointment_service or AppointmentService()

    def rank(
        self,
        candidate_options: Iterable[Dict[str, Any]],
        preference: Dict[str, Any],
        service_type: str | None,
        recalled_preferences: Dict[str, Any] | None = None,
        excluded_technician_ids: Iterable[int] | None = None,
    ) -> List[Dict[str, Any]]:
        excluded = {int(value) for value in (excluded_technician_ids or []) if str(value).isdigit()}
        recalled = recalled_preferences or {}
        ranked = []

        for option in candidate_options:
            technician = self._load_technician(option)
            if not technician:
                continue
            technician_id = int(technician["id"])
            if technician_id in excluded:
                continue

            preference_score, preference_matches = self._preference_score(
                technician.get("strength") or "",
                preference,
            )
            service_score, service_matches = self._service_score(
                technician.get("strength") or "",
                service_type,
            )
            history_score, history_matches = self._history_score(technician, recalled)
            total = round(
                min(1.0, preference_score * 0.55 + service_score * 0.30 + history_score * 0.15),
                4,
            )
            matched_features = list(dict.fromkeys(preference_matches + service_matches + history_matches))
            ranked.append(
                {
                    **option,
                    "technician_id": technician_id,
                    "technician_name": technician.get("name"),
                    "gender": technician.get("gender"),
                    "strength": technician.get("strength"),
                    "score": total,
                    "score_breakdown": {
                        "preference": round(preference_score, 4),
                        "service": round(service_score, 4),
                        "history": round(history_score, 4),
                    },
                    "matched_features": matched_features,
                }
            )

        return sorted(
            ranked,
            key=lambda item: (-item["score"], int(item["technician_id"])),
        )

    def _load_technician(self, option: Dict[str, Any]) -> Dict[str, Any] | None:
        technician_id = option.get("technician_id")
        if technician_id:
            technician = self.appointment_service.get_technician_by_id(int(technician_id))
            if technician:
                return technician
        name = option.get("technician_name")
        return self.appointment_service.get_technician_by_name(str(name)) if name else None

    @staticmethod
    def _preference_score(strength: str, preference: Dict[str, Any]) -> tuple[float, List[str]]:
        profile_key = preference.get("profile")
        raw_text = str(preference.get("raw_text") or "")
        if not profile_key:
            direct_matches = [
                token for token in _meaningful_tokens(raw_text)
                if token in strength
            ]
            return (0.65 if direct_matches else 0.5), direct_matches

        profile = PREFERENCE_PROFILES[profile_key]
        positive = [term for term in profile["positive_terms"] if term in strength]
        negative = [term for term in profile["negative_terms"] if term in strength]
        score = 0.5 + min(0.45, len(positive) * 0.14) - min(0.35, len(negative) * 0.12)
        return max(0.0, min(1.0, score)), positive

    @staticmethod
    def _service_score(strength: str, service_type: str | None) -> tuple[float, List[str]]:
        if not service_type:
            return 0.5, []
        terms = SERVICE_TERMS.get(service_type, ())
        matches = [term for term in terms if term in strength]
        if service_type in strength:
            matches.insert(0, service_type)
        score = 0.45 + min(0.5, len(matches) * 0.12)
        return min(1.0, score), matches

    @staticmethod
    def _history_score(
        technician: Dict[str, Any],
        recalled: Dict[str, Any],
    ) -> tuple[float, List[str]]:
        matches = []
        score = 0.4
        if recalled.get("preferred_technician_id") == technician.get("id"):
            score = 1.0
            matches.append("符合历史常选技师")
        elif recalled.get("preferred_technician_name") == technician.get("name"):
            score = 1.0
            matches.append("符合历史常选技师")
        return score, matches


def _meaningful_tokens(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]+", text.lower())
        if token not in {"帮我", "一个", "技师", "推荐", "一点", "可以"}
    ]

