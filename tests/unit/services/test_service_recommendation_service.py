from services.service_recommendation_service import ServiceRecommendationService


def test_service_recommendation_prefers_complete_symptom_keywords():
    result = ServiceRecommendationService().recommend("我最近有点乏力")

    selected = result["selected"]
    assert selected["name"] == "全身推拿"
    assert "乏力" in selected["matched_keywords"]
    assert "乏" not in selected["matched_keywords"]
