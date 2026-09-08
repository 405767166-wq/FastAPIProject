"""MySQL 存储实现（M10 V2：MySQL + SQLAlchemy）。

对标 backend/db/init.sql 的四张表：
    meeting_records        会议记录主表（每场会议一行）
    meeting_transcripts    会议转录（一场会议一行）
    meeting_word_frequency 词频明细（一场会议多行）
    meeting_summaries      会议总结（一场会议一行）

所有方法满足 app/store/base.py 的 MeetingStore 抽象；与 MemoryStore 对外返回
完全一致的"会议记录 dict"（含 transcript/summary 等字段），因此上层 API/worker
无需感知存储后端。

要点：
    - meeting_id 为业务主键（uuid4().hex），四表以其关联；子表以 meeting_id 外键
      引用主表并 ON DELETE CASCADE（删除会议自动清转录/词频/总结）。
    - 写入均以 meeting_id 为幂等键：转录/总结 一对一 upsert；词频为整表覆盖。
    - created_at/updated_at 默认本地时间（naive），与 init.sql 的 CURRENT_TIMESTAMP 一致。

启用条件（app/config.py）：配置了 `MYSQL_HOST`，storage_backend 即返回 "mysql"。
本类不感知后端选择，由 main.py 的 build_store() 按 settings 决定使用。
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    create_engine,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.engine import URL, Engine
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from app.config import settings
from app.store.base import MeetingStore

logger = logging.getLogger(__name__)

# create_meeting/update_meeting 可接受的"主表"字段（其余字段路由到转录/总结子表）。
_RECORD_FIELDS = frozenset({
    "title", "file_name", "file_path", "file_size",
    "duration_sec", "chunk_count", "status", "progress", "stage", "error_message",
})


def _now() -> datetime:
    """本地时间（naive datetime），写入 DATETIME 列，与 init.sql 的 CURRENT_TIMESTAMP 一致。"""
    return datetime.now().replace(microsecond=0)


# 主键类型：MySQL 用 BIGINT（与 init.sql 一致）；SQLite 用 INTEGER（触发行号自增，
# 便于用内存库做验证/测试）。
BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")

# 转写正文字段：MySQL 用 LONGTEXT（与 init.sql 一致，支持长文）；其他库用 TEXT。
TRANSCRIPT_COL = Text().with_variant(LONGTEXT(), "mysql")


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


class MeetingRecord(Base):
    """meeting_records：会议记录主表（每场会议一行）。"""

    __tablename__ = "meeting_records"

    id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    meeting_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now,
    )

    __table_args__ = (Index("idx_status_created", "status", "created_at"),)


class MeetingTranscript(Base):
    """meeting_transcripts：会议转录（一场会议一行，meeting_id 唯一）。"""

    __tablename__ = "meeting_transcripts"

    id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    meeting_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("meeting_records.meeting_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    transcript: Mapped[str | None] = mapped_column(TRANSCRIPT_COL, nullable=True)
    asr_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now,
    )


class MeetingWordFrequency(Base):
    """meeting_word_frequency：词频明细（一场会议多行，(meeting_id, word) 唯一）。"""

    __tablename__ = "meeting_word_frequency"

    id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    meeting_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("meeting_records.meeting_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    word: Mapped[str] = mapped_column(String(64), nullable=False)
    freq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)

    __table_args__ = (
        Index("uk_meeting_word", "meeting_id", "word", unique=True),
        Index("idx_meeting_id", "meeting_id"),
    )


class MeetingSummary(Base):
    """meeting_summaries：会议总结（一场会议一行，meeting_id 唯一）。"""

    __tablename__ = "meeting_summaries"

    id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)
    meeting_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("meeting_records.meeting_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="template")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now,
    )


def _make_engine() -> Engine:
    """按 app.config.settings 的 MySQL 配置构造 SQLAlchemy 引擎。

    对连接串做 URL 参数化转义，避免密码含特殊字符时出错；charset=utf8mb4 保证中文。
    """
    url = URL.create(
        drivername="mysql+pymysql",
        username=settings.mysql_user or "root",
        password=settings.mysql_password or "",
        host=settings.mysql_host or "127.0.0.1",
        port=settings.mysql_port or 3306,
        database=settings.mysql_db or "meeting_minutes",
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600, echo=False)


class MySQLStore(MeetingStore):
    """基于四张表（backend/db/init.sql）的 MySQL 存储实现。

    每场会议以 meeting_id 关联四个模型；对外返回与 MemoryStore 一致的记录 dict，
    便于上层（API / worker）无感知切换。
    """

    def __init__(self, *, engine: Engine | None = None) -> None:
        self._engine = engine or _make_engine()
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,  # commit 后仍可读取对象属性，便于还原 dict
            autoflush=False,
        )
        # 建表兜底：若表已由 backend/db/init.sql 建好，create_all 为幂等空操作；
        # 若未建（开发期），则按模型自动创建。DB 不可达时仅告警，不阻断启动。
        try:
            Base.metadata.create_all(self._engine)
        except Exception:  # noqa: BLE001 - 启动阶段不因 DB 故障静默失败，改为告警
            logger.warning(
                "MySQL 建表跳过（可能数据库不可达）：%s",
                self._engine.url.database,
                exc_info=True,
            )

    # ---------- 会话管理 ----------

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """每操作一个独立会话，提交/回滚由上下文管理器统一兜底。"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------- 记录 ⇄ dict 双向转换 ----------

    @staticmethod
    def _dt(value: datetime | None) -> str | None:
        return value.isoformat(timespec="seconds") if value else None

    @classmethod
    def _row_dict(cls, record: MeetingRecord,
                  transcript: MeetingTranscript | None = None,
                  summary: MeetingSummary | None = None) -> dict:
        """把 ORM 记录还原为与 MemoryStore 一致的 dict（含 transcript/summary）。"""
        return {
            "id": record.id,
            "meeting_id": record.meeting_id,
            "title": record.title,
            "file_name": record.file_name,
            "file_path": record.file_path,
            "file_size": record.file_size,
            "status": record.status,
            "progress": record.progress,
            "stage": record.stage,
            "duration_sec": record.duration_sec,
            "chunk_count": record.chunk_count,
            "transcript": transcript.transcript if transcript else None,
            "summary": summary.summary if summary else None,
            "summary_is_mock": bool(summary.summary_is_mock) if summary else False,
            "model": summary.model if summary else None,
            "error_message": record.error_message,
            "created_at": cls._dt(record.created_at),
            "updated_at": cls._dt(record.updated_at),
        }

    # ---------- 会议 ----------

    def create_meeting(self, *, meeting_id: str, title: str, file_name: str,
                       file_path: str, file_size: int, **extra) -> dict:
        with self._session() as s:
            record = MeetingRecord(
                meeting_id=meeting_id,
                title=title or file_name,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
            )
            for key, value in extra.items():
                if key in _RECORD_FIELDS and hasattr(record, key):
                    setattr(record, key, value)
            s.add(record)
            s.flush()
            return self._row_dict(record)

    def get_meeting(self, meeting_id: str) -> dict | None:
        with self._session() as s:
            record = self._get_record(s, meeting_id)
            if record is None:
                return None
            transcript = self._get_transcript(s, meeting_id)
            summary = self._get_summary(s, meeting_id)
            return self._row_dict(record, transcript, summary)

    def list_meetings(self, page: int = 1, page_size: int = 10,
                      status: str | None = None,
                      keyword: str | None = None) -> tuple[int, list[dict]]:
        conds = []
        if status:
            conds.append(MeetingRecord.status == status)
        if keyword:
            kw = keyword.strip().lower()
            if kw:
                like = f"%{kw}%"
                conds.append(or_(
                    func.lower(MeetingRecord.title).like(like),
                    func.lower(MeetingRecord.meeting_id).like(like),
                ))

        with self._session() as s:
            total = s.execute(
                select(func.count()).select_from(MeetingRecord).where(*conds)
            ).scalar_one()

            rows = s.execute(
                select(MeetingRecord, MeetingTranscript, MeetingSummary)
                .outerjoin(MeetingTranscript,
                           MeetingTranscript.meeting_id == MeetingRecord.meeting_id)
                .outerjoin(MeetingSummary,
                           MeetingSummary.meeting_id == MeetingRecord.meeting_id)
                .where(*conds)
                .order_by(MeetingRecord.id.desc())
                .limit(page_size)
                .offset((page - 1) * page_size)
            ).all()

            items = [self._row_dict(rec, tr, sm) for rec, tr, sm in rows]
            return total, items

    def update_meeting(self, meeting_id: str, **fields) -> dict | None:
        with self._session() as s:
            record = self._get_record(s, meeting_id)
            if record is None:
                return None

            # 1) 主表字段直接更新
            for key, value in fields.items():
                if key in _RECORD_FIELDS and hasattr(record, key):
                    setattr(record, key, value)

            # 2) 转录字段 → meeting_transcripts（一对一 upsert）
            if "transcript" in fields or "asr_provider" in fields:
                transcript = self._get_transcript(s, meeting_id)
                if transcript is None:
                    transcript = MeetingTranscript(
                        meeting_id=meeting_id,
                        asr_provider=settings.asr_provider,
                    )
                    s.add(transcript)
                if "transcript" in fields:
                    transcript.transcript = fields["transcript"]
                if "asr_provider" in fields:
                    transcript.asr_provider = fields["asr_provider"]

            # 3) 总结字段 → meeting_summaries（一对一 upsert）
            if any(k in fields for k in ("summary", "summary_is_mock", "model")):
                summary = self._get_summary(s, meeting_id)
                if summary is None:
                    summary = MeetingSummary(meeting_id=meeting_id)
                    s.add(summary)
                if "summary" in fields:
                    summary.summary = fields["summary"]
                if "summary_is_mock" in fields:
                    summary.summary_is_mock = fields["summary_is_mock"]
                if "model" in fields:
                    summary.model = fields["model"]

            s.flush()
            transcript = self._get_transcript(s, meeting_id)
            summary = self._get_summary(s, meeting_id)
            return self._row_dict(record, transcript, summary)

    def delete_meeting(self, meeting_id: str) -> bool:
        with self._session() as s:
            record = self._get_record(s, meeting_id)
            if record is None:
                return False
            # 显式删除子表（外键亦为 CASCADE，双保险），再删主表。
            s.execute(delete(MeetingTranscript).where(MeetingTranscript.meeting_id == meeting_id))
            s.execute(delete(MeetingWordFrequency).where(MeetingWordFrequency.meeting_id == meeting_id))
            s.execute(delete(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id))
            s.delete(record)
            return True

    # ---------- 词频 ----------

    def save_words(self, meeting_id: str, items: list[dict]) -> None:
        with self._session() as s:
            s.execute(delete(MeetingWordFrequency)
                      .where(MeetingWordFrequency.meeting_id == meeting_id))
            for item in items:
                s.add(MeetingWordFrequency(
                    meeting_id=meeting_id,
                    word=str(item.get("word", "")).strip(),
                    freq=int(item.get("freq", 0)),
                ))

    def get_words(self, meeting_id: str) -> list[dict]:
        with self._session() as s:
            rows = s.execute(
                select(MeetingWordFrequency.word, MeetingWordFrequency.freq)
                .where(MeetingWordFrequency.meeting_id == meeting_id)
                .order_by(MeetingWordFrequency.freq.desc())
            ).all()
            return [{"word": word, "freq": freq} for word, freq in rows]

    # ---------- 内部查询助手 ----------

    @staticmethod
    def _get_record(s: Session, meeting_id: str) -> MeetingRecord | None:
        return s.execute(
            select(MeetingRecord).where(MeetingRecord.meeting_id == meeting_id)
        ).scalar_one_or_none()

    @staticmethod
    def _get_transcript(s: Session, meeting_id: str) -> MeetingTranscript | None:
        return s.execute(
            select(MeetingTranscript).where(MeetingTranscript.meeting_id == meeting_id)
        ).scalar_one_or_none()

    @staticmethod
    def _get_summary(s: Session, meeting_id: str) -> MeetingSummary | None:
        return s.execute(
            select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
        ).scalar_one_or_none()
