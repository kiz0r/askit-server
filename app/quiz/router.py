from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.database import get_async_db
from app.models.user import User
from app.quiz.schemas import QuizCreate, QuizOut, QuizUpdate
from app.quiz.services import quiz_service
from app.quiz.exceptions import QuizNotFoundError, QuizAccessDeniedError
from app.quiz.types import QuizId

router = APIRouter(tags=["Quiz"])


@router.post("", response_model=QuizOut, response_model_by_alias=True)
async def create_quiz(
    body: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    quiz = await quiz_service.create_quiz(db, current_user, body)
    return quiz


@router.get("", response_model=list[QuizOut], response_model_by_alias=True)
async def list_quizzes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    quizzes = await quiz_service.list_quizzes(db, current_user)
    return quizzes


@router.get("/{quiz_id}", response_model=QuizOut, response_model_by_alias=True)
async def get_quiz(quiz_id: QuizId, db: AsyncSession = Depends(get_async_db)):
    quiz = await quiz_service.get_quiz(db, quiz_id)
    if quiz is None:
        raise QuizNotFoundError()

    return quiz


@router.patch("/{quiz_id}", response_model=QuizOut, response_model_by_alias=True)
async def update_quiz(
    quiz_id: QuizId,
    body: QuizUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    quiz = await quiz_service.update_quiz(db, quiz_id, current_user, body)
    if quiz is None:
        raise QuizAccessDeniedError()
    return quiz


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: QuizId,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    success = await quiz_service.delete_quiz(db, quiz_id, current_user)
    if not success:
        raise QuizAccessDeniedError()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
