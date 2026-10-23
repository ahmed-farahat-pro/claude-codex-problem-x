from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FOURWEEKS_",
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )

    mode: Literal["deterministic", "gemini"] = "deterministic"
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "FOURWEEKS_GEMINI_API_KEY"),
    )
    gemini_model: str = "gemini-3.5-flash-lite"

    db_path: Path = BACKEND_DIR / "data" / "4weeks.db"
    content_dir: Path = BACKEND_DIR.parent / "content"

    dev_auth: bool = True
    dev_live_allowance_seconds: int = 7200

    max_session_seconds: int = 600
    idle_timeout_seconds: int = 300
    max_session_model_tokens: int = 200_000
    max_tool_calls_per_turn: int = 8

    cors_origins: str = "http://localhost:5173"

    def resolved(self) -> "Settings":
        """Resolve relative paths against the backend directory, not the shell's cwd."""
        updates = {}
        if not self.db_path.is_absolute():
            updates["db_path"] = (BACKEND_DIR / self.db_path).resolve()
        if not self.content_dir.is_absolute():
            updates["content_dir"] = (BACKEND_DIR / self.content_dir).resolve()
        return self.model_copy(update=updates)
