from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration using environment variables with sensible defaults."""

    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    database_file: str = "planner.db"
    planner_start_hour: int = 9
    planner_end_hour: int = 17
    default_block_minutes: int = 60

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / self.database_file}"


settings = Settings()
