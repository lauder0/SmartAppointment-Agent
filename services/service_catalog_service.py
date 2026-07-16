"""服务项目初始化和读取服务。"""

import logging
from typing import List, Dict, Any

from db.db_router import DatabaseRouter

logger = logging.getLogger(__name__)

DEFAULT_SERVICES: List[Dict[str, Any]] = [
    {
        "name": "全身推拿",
        "description": "舒缓全身肌肉疲劳，促进血液循环，适合久坐办公或体力劳动者。",
        "default_duration_minutes": 60,
        "price_cents": 12000,
    },
    {
        "name": "肩颈推拿",
        "description": "针对颈椎和肩部不适，缓解肩颈酸痛和僵硬。",
        "default_duration_minutes": 30,
        "price_cents": 8000,
    },
    {
        "name": "足底按摩",
        "description": "刺激足部穴位，缓解疲劳，改善睡眠质量。",
        "default_duration_minutes": 45,
        "price_cents": 10000,
    },
    {
        "name": "背部推拿",
        "description": "放松脊柱两侧肌肉，缓解背部酸胀与劳损。",
        "default_duration_minutes": 40,
        "price_cents": 9000,
    },
]


class ServiceCatalogService:
    """管理可预约服务项目。"""

    def __init__(self, db: DatabaseRouter | None = None):
        # Do not open SQLite during construction. The understanding layer and
        # slot defaults use this service for built-in catalog facts, and those
        # paths must stay free of database side effects.
        self._db = db
        self.default_services = [dict(service) for service in DEFAULT_SERVICES]

    @property
    def db(self) -> DatabaseRouter:
        if self._db is None:
            self._db = DatabaseRouter()
        return self._db

    def initialize_default_services(self) -> bool:
        try:
            existing = self.db.appointments.get_all_services()
            existing_names = {service["name"] for service in existing}
            for service in self.default_services:
                if service["name"] in existing_names:
                    continue
                self.db.appointments.add_service(**service)
                logger.info(f"初始化服务项目：{service['name']}")
            return True
        except Exception as e:
            logger.error(f"初始化服务项目失败：{e}")
            return False

    def get_all_services(self) -> List[Dict[str, Any]]:
        return self.db.appointments.get_all_services()
