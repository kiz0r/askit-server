from datetime import datetime, timezone, timedelta
from jwt import ExpiredSignatureError, InvalidTokenError as JWTInvalidTokenError
from app.settings import ENV_SETTINGS
from app.auth.exceptions import TokenExpiredError, InvalidTokenError
import jwt


class JWTService:
    def __init__(
        self,
        access_token_lifetime=3600,
        refresh_token_lifetime=60 * 60 * 24 * 7,
    ):
        self._access_secret = ENV_SETTINGS.JWT_ACCESS_SECRET
        self._refresh_secret = ENV_SETTINGS.JWT_REFRESH_SECRET
        self._algorithm = "HS256"
        self._access_token_lifetime = access_token_lifetime
        self._refresh_token_lifetime = refresh_token_lifetime

    def _create_token(
        self,
        subject: str,
        token_type: str,
        key: str,
        expires_in: int,
    ) -> str:
        now = datetime.now(timezone.utc)

        payload = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }

        return jwt.encode(payload, key, algorithm=self._algorithm)

    def create_access_token(self, user_id: str) -> str:
        return self._create_token(
            subject=user_id,
            token_type="access",
            key=self._access_secret,
            expires_in=self._access_token_lifetime,
        )

    def create_refresh_token(self, user_id: str) -> str:
        return self._create_token(
            subject=user_id,
            token_type="refresh",
            key=self._refresh_secret,
            expires_in=self._refresh_token_lifetime,
        )

    def verify_access_token(self, token: str) -> dict:
        return self._decode(token, self._access_secret, "access")

    def verify_refresh_token(self, token: str) -> dict:
        return self._decode(token, self._refresh_secret, "refresh")

    def _decode(self, token: str, key: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(token, key, algorithms=[self._algorithm])

            if payload.get("type") != expected_type:
                raise InvalidTokenError()

            return payload

        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTInvalidTokenError:
            raise InvalidTokenError()


jwt_service: JWTService = JWTService()
