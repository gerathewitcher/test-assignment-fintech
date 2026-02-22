from dishka import Provider, Scope, provide

from src.database import Database
from src.repository.directory import DirectoryRepositoryProtocol
from src.repository.directory.postgres import PostgresDirectoryRepository
from src.service import DirectoryService, DirectoryServiceProtocol


class DatabaseProvider(Provider):
    def __init__(self, dsn: str | None = None):
        super().__init__()
        self._dsn = dsn

    @provide(scope=Scope.APP)
    async def database(self) -> Database:
        db = Database(dsn=self._dsn)
        return db


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def directory_repository(self, database: Database) -> DirectoryRepositoryProtocol:
        return PostgresDirectoryRepository(database)

    @provide(scope=Scope.REQUEST)
    def directory_service(
        self,
        directory_repository: DirectoryRepositoryProtocol,
    ) -> DirectoryServiceProtocol:
        return DirectoryService(directory_repository=directory_repository)
