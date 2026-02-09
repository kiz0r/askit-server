from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.auth.router import router as auth_router
from app.user.router import router as user_router
from app.quiz.router import router as quiz_router
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    generic_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AskIt! API",
    version="dev",
    lifespan=lifespan,
    redirect_slashes=False,
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}"
    if route.tags
    else route.name,
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

origins = [
    "http://localhost:5173",  # TODO: Move to environment settings
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(user_router, prefix="/api/v1/user")
app.include_router(quiz_router, prefix="/api/v1/quiz")
