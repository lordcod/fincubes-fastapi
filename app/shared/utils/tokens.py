from abc import abstractmethod
import uuid
import datetime
from fastapi import Request
from tortoise import BaseDBAsyncClient
from tortoise.transactions import in_transaction
from jwtifypy import JWTManager
from app.models import RefreshToken, Session, User
from app.shared.utils.scopes.combine import combine_all_scopes, flatten_scopes
from app.shared.utils.session import get_session_info

REFRESH_EXPIRES_IN = datetime.timedelta(days=7)
ACCESS_EXPIRES_IN = datetime.timedelta(minutes=15)


class TokenManager:
    def __init__(self, request: Request, fresh: bool):
        self.request = request
        self.manager = JWTManager.with_issuer(
            request.url.path).with_audience("auth")
        self.fresh = fresh
        self.session_info = get_session_info(request)

    @abstractmethod
    async def get_session(self, user: User, using_db: BaseDBAsyncClient) -> Session:
        ...

    async def extract_token(self, user: User) -> tuple[str, str]:
        refresh_id = str(uuid.uuid4())
        access_id = str(uuid.uuid4())

        async with in_transaction() as ctx:
            session = await self.get_session(user, ctx)
            await self.create_refresh(refresh_id, access_id, session, ctx)

        refresh_token = self.create_refresh_token(user, refresh_id)
        access_token = self.create_access_token(
            user, access_id)
        return refresh_token, access_token

    async def create_refresh(
        self,
        refresh_id: str,
        access_id: str,
        session: Session,
        using_db: BaseDBAsyncClient
    ):
        now = datetime.datetime.now()
        return await RefreshToken.create(
            id=refresh_id,
            access_id=access_id,
            session=session,
            issued_at=now,
            expires_at=now + REFRESH_EXPIRES_IN,
            using_db=using_db,
            request_info=self.session_info
        )

    def create_refresh_token(
        self,
        user: User,
        jti: str
    ) -> str:
        return self.manager.create_refresh_token(
            user.id,
            expires_delta=REFRESH_EXPIRES_IN,
            jti=jti
        )

    def create_access_token(
        self,
        user: User,
        jti: str
    ) -> str:
        result = combine_all_scopes({}, [], user.scopes)
        flattened = flatten_scopes(result)
        return self.manager.create_access_token(
            user.id,
            expires_delta=ACCESS_EXPIRES_IN,
            fresh=self.fresh,
            jti=jti,
            scopes=flattened
        )


class LoginTokenManager(TokenManager):
    def __init__(self, request: Request):
        super().__init__(request, fresh=True)

    async def get_session(self, user: User, using_db: BaseDBAsyncClient) -> Session:
        session_id = str(uuid.uuid4())
        return await Session.create(
            id=session_id,
            user_id=user.id,
            using_db=using_db
        )


class RefreshTokenManager(TokenManager):
    def __init__(self, request: Request, refresh: RefreshToken):
        super().__init__(request,  fresh=False)
        self.refresh = refresh

    async def get_session(self, user: User, using_db: BaseDBAsyncClient) -> Session:
        now = datetime.datetime.now()
        self.refresh.revoked_at = now
        await self.refresh.save(using_db=using_db)
        return self.refresh.session
