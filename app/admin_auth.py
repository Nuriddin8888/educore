from starlette.requests import Request
from app.core.config import settings
from sqladmin.authentication import AuthenticationBackend



class AdminAuth(
    AuthenticationBackend
):

    async def login(
        self,
        request: Request
    ):

        form = await request.form()

        username = form.get("username")
        password = form.get("password")

        if (
            username == settings.ADMIN_PASSWORD
            and
            password == settings.ADMIN_PASSWORD
        ):
            request.session.update(
                {"token": "admin"}
            )

            return True

        return False

    async def logout(
        self,
        request: Request
    ):
        request.session.clear()

        return True

    async def authenticate(
        self,
        request: Request
    ):

        return request.session.get(
            "token"
        ) == "admin"
    

