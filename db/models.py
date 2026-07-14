from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base, relationship

from config.time_utils import utc_now_naive


Base = declarative_base()


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    gender = Column(String, nullable=True)
    strength = Column(String, nullable=True)
    schedules = relationship("TechnicianSchedule", back_populates="technician", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="technician")


class TechnicianSchedule(Base):
    __tablename__ = "technician_schedules"

    id = Column(Integer, primary_key=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    appointment_id = Column(Integer, nullable=True)
    technician = relationship("Technician", back_populates="schedules")

    __table_args__ = (
        Index("idx_schedules_technician_time", "technician_id", "start_time", "end_time", "status"),
        CheckConstraint("end_time > start_time", name="ck_schedules_end_after_start"),
    )


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_duration_minutes = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    appointments = relationship("Appointment", back_populates="service")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    appointment_no = Column(String, nullable=False, unique=True)
    user_id = Column(String, nullable=False, default="default_user")
    session_id = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    gender_preference = Column(String, nullable=True)
    status = Column(String, nullable=False, default="confirmed")
    source = Column(String, nullable=False, default="chat")
    notes = Column(Text, nullable=True)
    idempotency_key = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    technician = relationship("Technician", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

    __table_args__ = (
        Index("idx_appointments_technician_time", "technician_id", "start_time", "end_time", "status"),
        Index("idx_appointments_session", "session_id", "created_at"),
        Index("idx_appointments_user_time", "user_id", "start_time"),
        Index("idx_appointments_idempotency_key", "idempotency_key"),
        CheckConstraint("end_time > start_time", name="ck_appointments_end_after_start"),
    )


class TechnicianUnavailable(Base):
    __tablename__ = "technician_unavailable"

    id = Column(Integer, primary_key=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    technician = relationship("Technician")

    __table_args__ = (
        Index("idx_unavailable_technician_time", "technician_id", "start_time", "end_time"),
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    keywords = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    is_active = Column(Integer, default=1)


class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, default="default_user")
    action_type = Column(String, nullable=False)
    action_data = Column(JSON, nullable=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    technician = relationship("Technician")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, default="default_user")
    preference_type = Column(String, nullable=False)
    preference_value = Column(String, nullable=False)
    confidence_score = Column(Integer, default=1)
    last_updated = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class UserRecommendation(Base):
    __tablename__ = "user_recommendations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, default="default_user")
    recommendation_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    payload_json = Column(JSON, nullable=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    status = Column(String, nullable=False, default="generated")
    dedupe_key = Column(String, nullable=True)
    trigger_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_sent = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now_naive)
    sent_at = Column(DateTime, nullable=True)
    technician = relationship("Technician")
