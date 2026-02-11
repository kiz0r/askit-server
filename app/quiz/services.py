from datetime import datetime
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from attrs import frozen
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswer
from app.quiz.schemas import (
    QuizCreate,
    QuizOut,
    QuizUpdate,
    QuizSettingsOut,
    QuizQuestionOut,
    QuizAnswerOut,
)
from app.quiz.exceptions import InvalidQuizDataError
from app.quiz.types import QuizId, QuestionId, AnswerId

# Constants for estimated time calculation
READING_TIME_PER_QUESTION_MS = 5000  # 5 seconds per question for reading/comprehension
SAFETY_BUFFER_MULTIPLIER = 1.1  # 10% extra time to avoid feeling rushed


@frozen
class QuizService:
    """
    Immutable service for quiz-related business logic.
    Stateless service - all methods operate on provided dependencies.
    """

    def _to_quiz_id(self, value: str | UUID) -> QuizId:
        """
        Convert UUID to QuizId branded type.
        Private method for internal service use only.
        """
        if isinstance(value, UUID):
            return QuizId(str(value))
        return QuizId(value)

    def _to_question_id(self, value: str | UUID) -> QuestionId:
        """
        Convert UUID to QuestionId branded type.
        Private method for internal service use only.
        """
        if isinstance(value, UUID):
            return QuestionId(str(value))
        return QuestionId(value)

    def _to_answer_id(self, value: str | UUID) -> AnswerId:
        """
        Convert UUID to AnswerId branded type.
        Private method for internal service use only.
        """
        if isinstance(value, UUID):
            return AnswerId(str(value))
        return AnswerId(value)

    def _from_quiz_id(self, quiz_id: QuizId) -> UUID:
        """
        Convert QuizId branded type to UUID for database operations.
        Private method for internal service use only.
        """
        return UUID(quiz_id)

    def quiz_to_response(self, quiz: Quiz) -> QuizOut:
        """Convert Quiz model to QuizOut response schema."""
        # Calculate estimated time with human factors:
        # - Base time: configured time per question
        # - Reading buffer: additional time for reading/comprehension
        # - Safety buffer: extra time to avoid feeling rushed
        base_time = len(quiz.questions) * quiz.time_per_question
        reading_buffer = len(quiz.questions) * READING_TIME_PER_QUESTION_MS
        estimated_time = int((base_time + reading_buffer) * SAFETY_BUFFER_MULTIPLIER)

        # Build questions list with validation
        questions_out: List[QuizQuestionOut] = []
        for question in quiz.questions:
            if question.correct_answer_id is None:
                raise InvalidQuizDataError(
                    f"Question {question.question_id} missing correct_answer_id"
                )
            questions_out.append(
                QuizQuestionOut(
                    question_id=self._to_question_id(question.question_id),
                    text=question.text,
                    correct_answer_id=self._to_answer_id(question.correct_answer_id),
                    answers=[
                        QuizAnswerOut(
                            answer_id=self._to_answer_id(answer.answer_id),
                            text=answer.text,
                            is_correct=answer.is_correct,
                        )
                        for answer in question.answers
                    ],
                )
            )

        return QuizOut(
            quiz_id=self._to_quiz_id(quiz.quiz_id),
            title=quiz.title,
            description=quiz.description,
            settings=QuizSettingsOut(
                randomize_questions=quiz.randomize_questions,
                randomize_answers=quiz.randomize_answers,
                show_immediate_feedback=quiz.show_immediate_feedback,
                time_per_question=quiz.time_per_question,
                visibility=quiz.visibility,
                max_participants=quiz.max_participants,
            ),
            questions=questions_out,
            estimated_time=estimated_time,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )

    async def create_quiz(
        self, db: AsyncSession, user: User, data: QuizCreate
    ) -> QuizOut:
        quiz = Quiz(
            title=data.title,
            description=data.description,
            creator_id=user.id,
            randomize_questions=data.settings.randomize_questions,
            randomize_answers=data.settings.randomize_answers,
            show_immediate_feedback=data.settings.show_immediate_feedback,
            time_per_question=data.settings.time_per_question,
            visibility=data.settings.visibility,
            max_participants=data.settings.max_participants,
        )

        for quiz_index, question_data in enumerate(data.questions):
            question = QuizQuestion(text=question_data.text, quiz=quiz)
            answers_objs: List[QuizAnswer] = []
            correct_answer = None

            for a_index, answer_data in enumerate(question_data.answers):
                answer = QuizAnswer(
                    text=answer_data.text,
                    is_correct=answer_data.is_correct,
                    question=question,
                )
                answers_objs.append(answer)
                if answer_data.is_correct:
                    if correct_answer is not None:
                        raise InvalidQuizDataError(
                            f"Question {quiz_index + 1} has multiple correct answers. Only one is allowed."
                        )
                    correct_answer = answer

            if correct_answer is None:
                raise InvalidQuizDataError(
                    f"Question {quiz_index + 1} must have exactly one correct answer."
                )

            question.answers = answers_objs
            quiz.questions.append(question)

        db.add(quiz)
        await db.flush()

        # Set correct answer IDs after flush (need IDs)
        for question in quiz.questions:
            for answer in question.answers:
                if answer.is_correct:
                    question.correct_answer_id = answer.answer_id
                    break

        await db.commit()

        # Re-fetch with eager loading to avoid lazy loading issues
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == quiz.quiz_id)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.answers))
        )
        quiz = result.scalars().first()
        return self.quiz_to_response(quiz)

    async def get_quiz(self, db: AsyncSession, quiz_id: QuizId) -> QuizOut | None:
        try:
            uuid_val = self._from_quiz_id(quiz_id)
            result = await db.execute(
                select(Quiz)
                .where(Quiz.quiz_id == uuid_val)
                .options(
                    selectinload(Quiz.questions).selectinload(QuizQuestion.answers)
                )
            )
            quiz = result.scalars().first()
            if quiz is None:
                return None
            return self.quiz_to_response(quiz)
        except ValueError:
            # Invalid UUID format - treat as not found
            return None

    async def update_quiz(
        self, db: AsyncSession, quiz_id: QuizId, user: User, data: QuizUpdate
    ) -> QuizOut | None:
        uuid_val = self._from_quiz_id(quiz_id)
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == uuid_val)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.answers))
        )
        quiz = result.scalars().first()

        if quiz is None:
            return None

        # Check if user is the creator
        if quiz.creator_id != user.id:
            return None

        # Update fields if provided
        if data.title is not None:
            quiz.title = data.title
        if data.description is not None:
            quiz.description = data.description
        if data.settings is not None:
            quiz.randomize_questions = data.settings.randomize_questions
            quiz.randomize_answers = data.settings.randomize_answers
            quiz.show_immediate_feedback = data.settings.show_immediate_feedback
            quiz.time_per_question = data.settings.time_per_question
            quiz.visibility = data.settings.visibility
            quiz.max_participants = data.settings.max_participants

        # Update questions if provided
        if data.questions is not None:
            # Clear correct_answer_id references first to avoid FK constraint issues
            for question in quiz.questions:
                question.correct_answer_id = None
            await db.flush()

            # Delete existing questions (cascades to answers)
            for question in quiz.questions:
                await db.delete(question)
            quiz.questions.clear()
            await db.flush()

            # Add new questions and answers
            for quiz_index, question_data in enumerate(data.questions):
                question = QuizQuestion(text=question_data.text, quiz=quiz)
                answers_objs: List[QuizAnswer] = []
                correct_answer = None

                for answer_data in question_data.answers:
                    answer = QuizAnswer(
                        text=answer_data.text,
                        is_correct=answer_data.is_correct,
                        question=question,
                    )
                    answers_objs.append(answer)
                    if answer_data.is_correct:
                        if correct_answer is not None:
                            raise InvalidQuizDataError(
                                f"Question {quiz_index + 1} has multiple correct answers. Only one is allowed."
                            )
                        correct_answer = answer

                if correct_answer is None:
                    raise InvalidQuizDataError(
                        f"Question {quiz_index + 1} must have exactly one correct answer."
                    )

                question.answers = answers_objs
                quiz.questions.append(question)

            await db.flush()

            # Set correct answer IDs after flush (need IDs)
            for question in quiz.questions:
                for answer in question.answers:
                    if answer.is_correct:
                        question.correct_answer_id = answer.answer_id
                        break

        # Explicitly update timestamp (onupdate doesn't trigger for related changes)
        quiz.updated_at = datetime.utcnow()

        await db.commit()

        # Re-fetch with eager loading to avoid lazy loading issues
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == uuid_val)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.answers))
        )
        quiz = result.scalars().first()
        return self.quiz_to_response(quiz)

    async def delete_quiz(self, db: AsyncSession, quiz_id: QuizId, user: User) -> bool:
        uuid_val = self._from_quiz_id(quiz_id)
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == uuid_val)
            .options(selectinload(Quiz.questions))
        )
        quiz = result.scalars().first()

        if quiz is None:
            return False

        # Check if user is the creator
        if quiz.creator_id != user.id:
            return False

        # Clear correct_answer_id references to break circular FK dependency
        for question in quiz.questions:
            question.correct_answer_id = None
        await db.flush()

        await db.delete(quiz)
        await db.commit()
        return True

    async def list_quizzes(self, db: AsyncSession, user: User) -> List[QuizOut]:
        result = await db.execute(
            select(Quiz)
            .where(Quiz.creator_id == user.id)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.answers))
        )
        quizzes = result.scalars().all()
        return [self.quiz_to_response(quiz) for quiz in quizzes]


# Singleton instance
quiz_service = QuizService()
