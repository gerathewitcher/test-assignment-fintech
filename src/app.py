import uvicorn

# from database import Database
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.api.v1.directory import router
from src.config import settings
from src.dependencies import AppProvider, DatabaseProvider


class App:
    @staticmethod
    def create_fastapi_app():
        app = FastAPI(
            title="Directory API",
            description="API for organizations, buildings, activities and directory lookup.",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        app.include_router(router)
        return app

    async def run_fastapi(self):
        app = self.create_fastapi_app()

        container = make_async_container(AppProvider(), DatabaseProvider())
        # database = await container.get(Database)
        # await database.check_connection()
        setup_dishka(container, app)

        config = uvicorn.Config(app, host="0.0.0.0", port=settings.APP_PORT)
        server = uvicorn.Server(config)
        await server.serve()

    async def start(self):
        await self.run_fastapi()
