from datetime import datetime
from typing import Any, Dict, List, Optional

from config.time_utils import business_now_naive, utc_now_naive

from ..base.session_manager import SessionManager
from ..models import Appointment, Service, Technician, TechnicianSchedule, TechnicianUnavailable


class AppointmentRepository:
    """预约、服务项目和技师不可用时间的数据访问对象。"""

    ACTIVE_APPOINTMENT_STATUSES = ("pending", "confirmed")

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def add_service(
        self,
        name: str,
        default_duration_minutes: int,
        price_cents: int,
        description: Optional[str] = None,
    ) -> int:
        with self.session_manager.session_scope() as session:
            existing = session.query(Service).filter(Service.name == name).first()
            if existing:
                existing.description = description or existing.description
                existing.default_duration_minutes = default_duration_minutes
                existing.price_cents = price_cents
                existing.is_active = 1
                existing.updated_at = utc_now_naive()
                return existing.id

            service = Service(
                name=name,
                description=description,
                default_duration_minutes=default_duration_minutes,
                price_cents=price_cents,
            )
            session.add(service)
            session.flush()
            return service.id

    def get_service_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self.session_manager.session_scope() as session:
            service = session.query(Service).filter(
                Service.name == name,
                Service.is_active == 1,
            ).first()
            return self._service_to_dict(service) if service else None

    def get_all_services(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        with self.session_manager.session_scope() as session:
            query = session.query(Service)
            if not include_inactive:
                query = query.filter(Service.is_active == 1)
            return [self._service_to_dict(service) for service in query.all()]

    def create_appointment(
        self,
        appointment_no: str,
        technician_id: int,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        service_id: Optional[int] = None,
        gender_preference: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        source: str = "chat",
        notes: Optional[str] = None,
        status: str = "confirmed",
    ) -> int:
        with self.session_manager.session_scope() as session:
            appointment = Appointment(
                appointment_no=appointment_no,
                user_id=user_id or "default_user",
                session_id=session_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                technician_id=technician_id,
                service_id=service_id,
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                gender_preference=gender_preference,
                status=status,
                source=source,
                notes=notes,
            )
            session.add(appointment)
            session.flush()
            return appointment.id

    def create_appointment_with_schedule_atomic(
        self,
        appointment_no: str,
        technician_id: int,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        gender_preference: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        source: str = "chat",
        notes: Optional[str] = None,
        status: str = "confirmed",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create appointment and busy schedule in one transaction.

        Returns a structured result so callers can distinguish normal conflict
        failures from idempotent replays.
        """
        with self.session_manager.session_scope() as session:
            if idempotency_key:
                existing = session.query(Appointment).filter(
                    Appointment.idempotency_key == idempotency_key
                ).first()
                if existing:
                    return {
                        "success": True,
                        "created": False,
                        "reason": "idempotent_replay",
                        "appointment_id": existing.id,
                        "appointment_no": existing.appointment_no,
                    }

            technician = (
                session.query(Technician)
                .filter(Technician.id == technician_id)
                .with_for_update()
                .first()
            )
            if not technician:
                return {
                    "success": False,
                    "created": False,
                    "reason": "technician_not_found",
                }

            appointment_conflict = session.query(Appointment).filter(
                Appointment.technician_id == technician_id,
                Appointment.status.in_(self.ACTIVE_APPOINTMENT_STATUSES),
                Appointment.start_time < end_time,
                Appointment.end_time > start_time,
            ).first()
            if appointment_conflict:
                return {
                    "success": False,
                    "created": False,
                    "reason": "appointment_conflict",
                    "conflict_appointment_id": appointment_conflict.id,
                }

            unavailable_conflict = session.query(TechnicianUnavailable).filter(
                TechnicianUnavailable.technician_id == technician_id,
                TechnicianUnavailable.start_time < end_time,
                TechnicianUnavailable.end_time > start_time,
            ).first()
            if unavailable_conflict:
                return {
                    "success": False,
                    "created": False,
                    "reason": "technician_unavailable",
                    "conflict_unavailable_id": unavailable_conflict.id,
                }

            schedule_conflict = session.query(TechnicianSchedule).filter(
                TechnicianSchedule.technician_id == technician_id,
                TechnicianSchedule.status == "busy",
                TechnicianSchedule.start_time < end_time,
                TechnicianSchedule.end_time > start_time,
            ).first()
            if schedule_conflict:
                return {
                    "success": False,
                    "created": False,
                    "reason": "schedule_conflict",
                    "conflict_schedule_id": schedule_conflict.id,
                }

            service = session.query(Service).filter(
                Service.name == service_name,
                Service.is_active == 1,
            ).first()

            appointment = Appointment(
                appointment_no=appointment_no,
                user_id=user_id or "default_user",
                session_id=session_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                technician_id=technician_id,
                service_id=service.id if service else None,
                service_name=service_name,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                gender_preference=gender_preference,
                status=status,
                source=source,
                notes=notes,
                idempotency_key=idempotency_key,
            )
            session.add(appointment)
            session.flush()

            schedule = TechnicianSchedule(
                technician_id=technician_id,
                start_time=start_time,
                end_time=end_time,
                status="busy",
                appointment_id=appointment.id,
            )
            session.add(schedule)
            session.flush()

            return {
                "success": True,
                "created": True,
                "reason": "created",
                "appointment_id": appointment.id,
                "appointment_no": appointment.appointment_no,
                "schedule_id": schedule.id,
            }

    def get_user_appointments(
        self,
        user_id: str,
        limit: Optional[int] = None,
        statuses: tuple[str, ...] = ("confirmed", "completed"),
    ) -> List[Dict[str, Any]]:
        with self.session_manager.session_scope() as session:
            query = session.query(Appointment).filter(Appointment.user_id == (user_id or "default_user"))
            if statuses:
                query = query.filter(Appointment.status.in_(statuses))
            query = query.order_by(Appointment.start_time.desc(), Appointment.created_at.desc())
            if limit:
                query = query.limit(limit)
            appointments = query.all()
            return [self._appointment_to_dict(appointment) for appointment in appointments]

    def get_known_user_ids(self, days_back: Optional[int] = None) -> List[str]:
        with self.session_manager.session_scope() as session:
            query = session.query(Appointment.user_id).filter(Appointment.user_id.isnot(None)).distinct()
            if days_back:
                from datetime import timedelta

                cutoff_date = business_now_naive() - timedelta(days=days_back)
                query = query.filter(Appointment.start_time >= cutoff_date)
            return [row[0] for row in query.all() if row[0]]

    def has_appointment_conflict(self, technician_id: int, start_time: datetime, end_time: datetime) -> bool:
        with self.session_manager.session_scope() as session:
            conflict = session.query(Appointment).filter(
                Appointment.technician_id == technician_id,
                Appointment.status.in_(self.ACTIVE_APPOINTMENT_STATUSES),
                Appointment.start_time < end_time,
                Appointment.end_time > start_time,
            ).first()
            return conflict is not None

    def has_unavailable_conflict(self, technician_id: int, start_time: datetime, end_time: datetime) -> bool:
        with self.session_manager.session_scope() as session:
            conflict = session.query(TechnicianUnavailable).filter(
                TechnicianUnavailable.technician_id == technician_id,
                TechnicianUnavailable.start_time < end_time,
                TechnicianUnavailable.end_time > start_time,
            ).first()
            return conflict is not None

    def add_unavailable_block(
        self,
        technician_id: int,
        start_time: datetime,
        end_time: datetime,
        reason: Optional[str] = None,
    ) -> int:
        with self.session_manager.session_scope() as session:
            block = TechnicianUnavailable(
                technician_id=technician_id,
                start_time=start_time,
                end_time=end_time,
                reason=reason,
            )
            session.add(block)
            session.flush()
            return block.id

    def _service_to_dict(self, service: Service) -> Dict[str, Any]:
        return {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "default_duration_minutes": service.default_duration_minutes,
            "price_cents": service.price_cents,
            "is_active": bool(service.is_active),
            "created_at": service.created_at,
            "updated_at": service.updated_at,
        }

    def _appointment_to_dict(self, appointment: Appointment) -> Dict[str, Any]:
        technician = appointment.technician
        return {
            "id": appointment.id,
            "appointment_no": appointment.appointment_no,
            "user_id": appointment.user_id,
            "session_id": appointment.session_id,
            "technician_id": appointment.technician_id,
            "technician_name": technician.name if technician else None,
            "technician_gender": technician.gender if technician else None,
            "technician_strength": technician.strength if technician else None,
            "service_id": appointment.service_id,
            "service_name": appointment.service_name,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "duration_minutes": appointment.duration_minutes,
            "gender_preference": appointment.gender_preference,
            "status": appointment.status,
            "source": appointment.source,
            "idempotency_key": appointment.idempotency_key,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
            "cancelled_at": appointment.cancelled_at,
            "cancel_reason": appointment.cancel_reason,
        }
