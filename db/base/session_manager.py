from contextlib import contextmanager
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from ..models import Base


class SessionManager:
    """
    数据库会话管理器
    
    职责：
    1. 管理数据库连接和会话
    2. 提供统一的会话上下文管理
    3. 处理事务和异常回滚
    """
    
    def __init__(self, db_path='sqlite:///data/smart_appointment.db'):
        """
        初始化会话管理器
        
        Args:
            db_path: 数据库连接路径
        """
        connect_args = {}
        if db_path.startswith("sqlite"):
            connect_args["timeout"] = 30
        self.engine = create_engine(db_path, connect_args=connect_args)
        if self.engine.dialect.name == "sqlite":
            self._configure_sqlite_pragmas()
        Base.metadata.create_all(self.engine)
        self._ensure_lightweight_migrations()
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def _configure_sqlite_pragmas(self):
        """Configure SQLite for safer local concurrent writes."""

        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    def _ensure_lightweight_migrations(self):
        """Add newly introduced columns for existing local SQLite databases."""
        if self.engine.dialect.name != "sqlite":
            return

        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())
        migrations = {
            "appointments": {
                "user_id": "VARCHAR DEFAULT 'default_user' NOT NULL",
                "idempotency_key": "VARCHAR",
            },
            "user_recommendations": {
                "payload_json": "JSON",
                "status": "VARCHAR DEFAULT 'generated' NOT NULL",
                "dedupe_key": "VARCHAR",
                "trigger_reason": "TEXT",
                "expires_at": "DATETIME",
            },
        }
        with self.engine.begin() as connection:
            for table_name, columns in migrations.items():
                if table_name not in existing_tables:
                    continue
                existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
                for column_name, ddl in columns.items():
                    if column_name not in existing_columns:
                        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))
            if "appointments" in existing_tables:
                connection.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_idempotency_key ON appointments (idempotency_key)")
                )
            if "technician_schedules" in existing_tables:
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_schedules_technician_time "
                        "ON technician_schedules (technician_id, start_time, end_time, status)"
                    )
                )

    @contextmanager
    def session_scope(self):
        """
        提供会话上下文管理
        
        自动处理：
        - 会话创建和关闭
        - 事务提交和回滚
        - 异常处理
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """关闭会话管理器"""
        self.Session.remove()
        self.engine.dispose()
