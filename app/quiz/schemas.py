from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum
from app.quiz.types import QuizId, QuestionId, AnswerId

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
    answers: List[QuizAnswerCreate]


class QuizSettingsCreate(BaseModel):
    randomize_questions: bool = Field(
        default=False,
        serialization_alias="randomizeQuestions",
        validation_alias="randomizeQuestions",
    )
    randomize_answers: bool = Field(
        default=False,
        serialization_alias="randomizeAnswers",
        validation_alias="randomizeAnswers",
    )
    show_immediate_feedback: bool = Field(
        default=False,
        serialization_alias="showImmediateFeedback",
        validation_alias="showImmediateFeedback",
    )
    time_per_question: int = Field(
        default=DEFAULT_TIME_PER_QUESTION_MS,
        serialization_alias="timePerQuestion",
        validation_alias="timePerQuestion",
        description="Time per question in milliseconds",
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
    settings: QuizSettingsCreate
    questions: List[QuizQuestionCreate]


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[QuizSettingsCreate] = None
    questions: Optional[List[QuizQuestionCreate]] = None


class QuizAnswerOut(BaseModel):
    answer_id: AnswerId = Field(serialization_alias="answerId")
    text: str
    is_correct: bool = Field(default=False, serialization_alias="isCorrect")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizQuestionOut(BaseModel):
    question_id: QuestionId = Field(serialization_alias="questionId")
    text: str
    correct_answer_id: AnswerId = Field(serialization_alias="correctAnswerId")
    answers: List[QuizAnswerOut]

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizSettingsOut(BaseModel):
    randomize_questions: bool = Field(serialization_alias="randomizeQuestions")
    randomize_answers: bool = Field(serialization_alias="randomizeAnswers")
    show_immediate_feedback: bool = Field(serialization_alias="showImmediateFeedback")
    time_per_question: int = Field(serialization_alias="timePerQuestion")
    visibility: QuizVisibility
    max_participants: int = Field(serialization_alias="maxParticipants")

    model_config = ConfigDict(populate_by_name=True)


class QuizOut(BaseModel):
    quiz_id: QuizId = Field(serialization_alias="quizId")
    title: str
    description: Optional[str] = None
    settings: QuizSettingsOut
    questions: List[QuizQuestionOut]
    estimated_time: int = Field(
        serialization_alias="estimatedTime",
        description="Estimated time to complete the quiz in milliseconds",
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QuizListOut(BaseModel):
    items: List[QuizOut]
