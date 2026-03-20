from datetime import datetime
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from attrs import frozen
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswer, Tag
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
        # Build questions list
        questions_out: List[QuizQuestionOut] = []
        for question in quiz.questions:
            questions_out.append(
                QuizQuestionOut(
                    question_id=self._to_question_id(question.question_id),
                    text=question.text,
                    position=question.position,
                    time_limit=question.time_limit,
                    is_hidden=question.is_hidden,
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

        # Calculate estimated time: sum of time_limits for non-hidden questions
        estimated_time = sum(q.time_limit for q in quiz.questions if not q.is_hidden)

        # Extract tag names
        tags = [tag.name for tag in quiz.tags] if quiz.tags else []

        return QuizOut(
            quiz_id=self._to_quiz_id(quiz.quiz_id),
            title=quiz.title,
            description=quiz.description,
            tags=tags,
            settings=QuizSettingsOut(
                randomize_answers=quiz.randomize_answers,
                default_time_per_question=quiz.default_time_per_question,
                visibility=quiz.visibility,
                max_participants=quiz.max_participants,
            ),
            questions=questions_out,
            estimated_time=estimated_time,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )

    async def _get_or_create_tags(
        self, db: AsyncSession, tag_names: List[str]
    ) -> List[Tag]:
        """Get existing tags or create new ones."""
        if not tag_names:
            return []

        tags = []
        for name in tag_names:
            result = await db.execute(select(Tag).where(Tag.name == name))
            tag = result.scalars().first()
            if tag is None:
                tag = Tag(name=name)
                db.add(tag)
            tags.append(tag)
        return tags

    async def create_quiz(
        self, db: AsyncSession, user: User, data: QuizCreate
    ) -> QuizOut:
        # Get or create tags
        tags = await self._get_or_create_tags(db, data.tags)

        quiz = Quiz(
            title=data.title,
            description=data.description,
            creator_id=user.id,
            randomize_answers=data.settings.randomize_answers,
            default_time_per_question=data.settings.default_time_per_question,
            visibility=data.settings.visibility,
            max_participants=data.settings.max_participants,
            tags=tags,
        )

        for position, question_data in enumerate(data.questions, start=1):
            question = QuizQuestion(
                text=question_data.text,
                position=position,
                time_limit=question_data.time_limit,
                is_hidden=question_data.is_hidden,
                quiz=quiz,
            )
            answers_objs: List[QuizAnswer] = []
            correct_answers = []

            for answer_data in question_data.answers:
                answer = QuizAnswer(
                    text=answer_data.text,
                    is_correct=answer_data.is_correct,
                    question=question,
                )
                answers_objs.append(answer)
                if answer_data.is_correct:
                    correct_answers.append(answer)

            if not correct_answers:
                raise InvalidQuizDataError(
                    f"Question {position} must have at least one correct answer."
                )

            question.answers = answers_objs
            quiz.questions.append(question)

        db.add(quiz)
        await db.commit()

        # Re-fetch with eager loading to avoid lazy loading issues
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == quiz.quiz_id)
            .options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                selectinload(Quiz.tags),
            )
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
                    selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                    selectinload(Quiz.tags),
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
            .options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                selectinload(Quiz.tags),
            )
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
        if data.tags is not None:
            quiz.tags = await self._get_or_create_tags(db, data.tags)
        if data.settings is not None:
            quiz.randomize_answers = data.settings.randomize_answers
            quiz.default_time_per_question = data.settings.default_time_per_question
            quiz.visibility = data.settings.visibility
            quiz.max_participants = data.settings.max_participants

        # Update questions if provided
        if data.questions is not None:
            # Delete existing questions (cascades to answers)
            for question in quiz.questions:
                await db.delete(question)
            quiz.questions.clear()
            await db.flush()

            # Add new questions and answers
            for position, question_data in enumerate(data.questions, start=1):
                question = QuizQuestion(
                    text=question_data.text,
                    position=position,
                    time_limit=question_data.time_limit,
                    is_hidden=question_data.is_hidden,
                    quiz=quiz,
                )
                answers_objs: List[QuizAnswer] = []
                correct_answers = []

                for answer_data in question_data.answers:
                    answer = QuizAnswer(
                        text=answer_data.text,
                        is_correct=answer_data.is_correct,
                        question=question,
                    )
                    answers_objs.append(answer)
                    if answer_data.is_correct:
                        correct_answers.append(answer)

                if not correct_answers:
                    raise InvalidQuizDataError(
                        f"Question {position} must have at least one correct answer."
                    )

                question.answers = answers_objs
                quiz.questions.append(question)

        # Explicitly update timestamp (onupdate doesn't trigger for related changes)
        quiz.updated_at = datetime.utcnow()

        await db.commit()

        # Re-fetch with eager loading to avoid lazy loading issues
        result = await db.execute(
            select(Quiz)
            .where(Quiz.quiz_id == uuid_val)
            .options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                selectinload(Quiz.tags),
            )
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

        await db.delete(quiz)
        await db.commit()
        return True

    async def list_quizzes(self, db: AsyncSession, user: User) -> List[QuizOut]:
        result = await db.execute(
            select(Quiz)
            .where(Quiz.creator_id == user.id)
            .options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.answers),
                selectinload(Quiz.tags),
            )
        )
        quizzes = result.scalars().all()
        return [self.quiz_to_response(quiz) for quiz in quizzes]


# Singleton instance
quiz_service = QuizService()
