from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration using environment variables with sensible defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    database_file: str = "planner.db"
    planner_start_hour: int = 9
    planner_end_hour: int = 17
    default_block_minutes: int = 20
    home_location_name: str = "Home Base"
    home_location_address: str | None = None
    google_maps_api_key: str | None = None

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / self.database_file}"


settings = Settings()
