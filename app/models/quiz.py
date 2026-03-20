import enum
import uuid
from app.quiz.schemas import QuizVisibility
from sqlalchemy import (
    UUID,
    Column,
    Integer,
    Boolean,
    ForeignKey,
    Enum,
    DateTime,
    VARCHAR,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Literal
from app.database import Base


class QuizSettingsSchema(BaseModel):
    randomize_answers: bool = False
    default_time_per_question: int = 30_000
    visibility: Literal["public", "private"]
    max_participants: Optional[int] = None


# Many-to-many association table for Quiz <-> Tag
quiz_tags = Table(
    "quiz_tags",
    Base.metadata,
    Column("quiz_id", UUID, ForeignKey("quizzes.quiz_id"), primary_key=True),
    Column("tag_id", UUID, ForeignKey("tags.tag_id"), primary_key=True),
)


class Tag(Base):
    """Tags for categorizing quizzes."""

    __tablename__ = "tags"

    tag_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    name = Column(VARCHAR(30), nullable=False, unique=True, index=True)

    quizzes = relationship("Quiz", secondary=quiz_tags, back_populates="tags")


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    creator_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="quizzes")

    title = Column(VARCHAR(50), nullable=False)
    description = Column(VARCHAR(300), nullable=True)

    # Settings (randomize_questions, show_immediate_feedback moved to room/session level)
    randomize_answers = Column(Boolean, default=False)
    default_time_per_question = Column(
        Integer, default=30_000
    )  # UI preset, milliseconds
    visibility = Column(
        Enum(QuizVisibility, name="quiz_visibility"),
        nullable=False,
        default=QuizVisibility.public,
    )
    max_participants = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.position",
    )
    sessions = relationship("QuizSession", back_populates="quiz")
    tags = relationship("Tag", secondary=quiz_tags, back_populates="quizzes")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    question_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    quiz_id = Column(UUID, ForeignKey("quizzes.quiz_id"), nullable=False, index=True)
    text = Column(VARCHAR(255), nullable=False)
    position = Column(
        Integer, nullable=False, default=1
    )  # For drag & drop ordering (1-indexed)
    time_limit = Column(
        Integer, nullable=False, default=30_000
    )  # Per-question time in ms
    is_hidden = Column(Boolean, nullable=False, default=False)  # Hide from game

    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship(
        "QuizAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        foreign_keys="QuizAnswer.question_id",
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    answer_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    question_id = Column(
        UUID,
        ForeignKey("quiz_questions.question_id", name="fk_answer_question"),
        nullable=False,
    )
    text = Column(VARCHAR(255), nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)

    question = relationship(
        "QuizQuestion", back_populates="answers", foreign_keys=[question_id]
    )


class QuizSessionStatus(enum.Enum):
    waiting = "waiting"
    in_progress = "in_progress"
    finished = "finished"


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    quiz_id = Column(UUID, ForeignKey("quizzes.quiz_id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(
        Enum(QuizSessionStatus, name="quiz_session_status"),
        nullable=False,
        default=QuizSessionStatus.waiting,
    )
    quiz = relationship("Quiz", back_populates="sessions")
    participants = relationship("QuizParticipant", back_populates="session")


class QuizParticipant(Base):
    __tablename__ = "quiz_participants"

    participant_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    session_id = Column(UUID, ForeignKey("quiz_sessions.session_id"), nullable=False)
    anonymous_user_id = Column(UUID, ForeignKey("anonymous_users.id"), nullable=False)

    nickname = Column(VARCHAR(50), nullable=False)
    score = Column(Integer, default=0)
    is_connected = Column(Boolean, default=True)

    session = relationship("QuizSession", back_populates="participants")
