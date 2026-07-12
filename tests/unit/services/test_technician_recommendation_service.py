from services.technician_recommendation_service import (
    TechnicianRecommendationService,
    parse_recommendation_preference,
)


class FakeAppointmentService:
    technicians = {
        1: {
            "id": 1,
            "name": "张伟",
            "gender": "男",
            "strength": "擅长深层组织按摩，力气大，善于肌肉深层放松",
        },
        2: {
            "id": 2,
            "name": "李娜",
            "gender": "女",
            "strength": "手法细腻，擅长舒缓放松，适合压力大、睡眠差人群",
        },
        3: {
            "id": 3,
            "name": "赵敏",
            "gender": "女",
            "strength": "精通经络推拿，善于调理亚健康，力气适中",
        },
    }

    def get_technician_by_id(self, technician_id):
        return self.technicians.get(technician_id)

    def get_technician_by_name(self, name):
        return next(
            (technician for technician in self.technicians.values() if technician["name"] == name),
            None,
        )


def _options():
    return [
        {"technician_id": 1, "technician_name": "张伟"},
        {"technician_id": 2, "technician_name": "李娜"},
        {"technician_id": 3, "technician_name": "赵敏"},
    ]


def test_strong_preference_ranks_strong_technician_first():
    preference = parse_recommendation_preference("我想要力气大一点的")
    service = TechnicianRecommendationService(FakeAppointmentService())

    ranked = service.rank(_options(), preference, "全身推拿")

    assert ranked[0]["technician_name"] == "张伟"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "力气大" in ranked[0]["matched_features"]


def test_gentle_preference_ranks_relaxation_technician_first():
    preference = parse_recommendation_preference("希望手法轻一点，主要想舒缓放松")
    service = TechnicianRecommendationService(FakeAppointmentService())

    ranked = service.rank(_options(), preference, "全身推拿")

    assert ranked[0]["technician_name"] == "李娜"
    assert "手法细腻" in ranked[0]["matched_features"]


def test_excluded_technician_is_not_recommended_again():
    preference = parse_recommendation_preference("力气大一点")
    service = TechnicianRecommendationService(FakeAppointmentService())

    ranked = service.rank(
        _options(),
        preference,
        "全身推拿",
        excluded_technician_ids=[1],
    )

    assert all(candidate["technician_id"] != 1 for candidate in ranked)

