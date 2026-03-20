from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from enum import Enum
from app.quiz.types import QuizId, QuestionId, AnswerId
from app.quiz.exceptions import InvalidQuizDataError

# Validation constants
MAX_TITLE_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 300
MAX_TAG_LENGTH = 30
MAX_TAGS_PER_QUIZ = 5

# Constants
DEFAULT_MAX_PARTICIPANTS = 5
MAX_PARTICIPANTS_LIMIT = 30
DEFAULT_TIME_PER_QUESTION_MS = 30000  # Default time per question in milliseconds


class QuizVisibility(str, Enum):
    private = "private"
    public = "public"


class QuizAnswerCreate(BaseModel):
    text: str
    is_correct: bool = Field(
        default=False, serialization_alias="isCorrect", validation_alias="isCorrect"
    )

    model_config = ConfigDict(populate_by_name=True)


class QuizQuestionCreate(BaseModel):
    text: str
    time_limit: int = Field(
        default=DEFAULT_TIME_PER_QUESTION_MS,
        ge=5000,  # Minimum 5 seconds
        le=300000,  # Maximum 5 minutes
        serialization_alias="timeLimit",
        validation_alias="timeLimit",
        description="Time limit for this question in milliseconds",
    )
    is_hidden: bool = Field(
        default=False,
        serialization_alias="isHidden",
        validation_alias="isHidden",
    )
    answers: List[QuizAnswerCreate]

    model_config = ConfigDict(populate_by_name=True)


class QuizSettingsCreate(BaseModel):
    randomize_answers: bool = Field(
        default=False,
        serialization_alias="randomizeAnswers",
        validation_alias="randomizeAnswers",
    )
    default_time_per_question: int = Field(
        default=DEFAULT_TIME_PER_QUESTION_MS,
        serialization_alias="defaultTimePerQuestion",
        validation_alias="defaultTimePerQuestion",
        description="Default time per question in milliseconds (UI preset for new questions)",
    )
    visibility: QuizVisibility = QuizVisibility.public
    max_participants: int = Field(
        default=DEFAULT_MAX_PARTICIPANTS,
        ge=1,
        le=MAX_PARTICIPANTS_LIMIT,
        serialization_alias="maxParticipants",
        validation_alias="maxParticipants",
    )

    model_config = ConfigDict(populate_by_name=True)


class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    settings: QuizSettingsCreate
    questions: List[QuizQuestionCreate]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise InvalidQuizDataError("Quiz title is required")
        if len(v) > MAX_TITLE_LENGTH:
            raise InvalidQuizDataError(
                f"Quiz title must not exceed {MAX_TITLE_LENGTH} characters"
            )
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise InvalidQuizDataError(
                f"Quiz description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        validated = []
        for tag in v:
            tag = tag.strip().lower()
            if tag and len(tag) <= MAX_TAG_LENGTH:
                validated.append(tag)
        unique_tags = list(set(validated))
        if len(unique_tags) > MAX_TAGS_PER_QUIZ:
            raise InvalidQuizDataError(
                f"Maximum {MAX_TAGS_PER_QUIZ} tags allowed per quiz"
            )
        return unique_tags


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[QuizSettingsCreate] = None
    questions: Optional[List[QuizQuestionCreate]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise InvalidQuizDataError("Quiz title cannot be empty")
        if len(v) > MAX_TITLE_LENGTH:
            raise InvalidQuizDataError(
                f"Quiz title must not exceed {MAX_TITLE_LENGTH} characters"
            )
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise InvalidQuizDataError(
                f"Quiz description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        validated = []
        for tag in v:
            tag = tag.strip().lower()
            if tag and len(tag) <= MAX_TAG_LENGTH:
                validated.append(tag)
        unique_tags = list(set(validated))
        if len(unique_tags) > MAX_TAGS_PER_QUIZ:
            raise InvalidQuizDataError(
                f"Maximum {MAX_TAGS_PER_QUIZ} tags allowed per quiz"
            )
        return unique_tags


class QuizAnswerOut(BaseModel):
    answer_id: AnswerId = Field(serialization_alias="answerId")
    text: str
    is_correct: bool = Field(default=False, serialization_alias="isCorrect")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizQuestionOut(BaseModel):
    question_id: QuestionId = Field(serialization_alias="questionId")
    text: str
    position: int
    time_limit: int = Field(serialization_alias="timeLimit")
    is_hidden: bool = Field(serialization_alias="isHidden")
    answers: List[QuizAnswerOut]

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizSettingsOut(BaseModel):
    randomize_answers: bool = Field(serialization_alias="randomizeAnswers")
    default_time_per_question: int = Field(serialization_alias="defaultTimePerQuestion")
    visibility: QuizVisibility
    max_participants: int = Field(serialization_alias="maxParticipants")

    model_config = ConfigDict(populate_by_name=True)


class QuizOut(BaseModel):
    quiz_id: QuizId = Field(serialization_alias="quizId")
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    settings: QuizSettingsOut
    questions: List[QuizQuestionOut]
    estimated_time: int = Field(
        serialization_alias="estimatedTime",
        description="Estimated time to complete the quiz in milliseconds (sum of non-hidden questions)",
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizListOut(BaseModel):
    items: List[QuizOut]
