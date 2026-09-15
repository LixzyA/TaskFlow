"""Pydantic input models for TaskFlow configuration."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    command: str = Field(min_length=1)
    timeout: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    dependencies: list[str] = Field(default_factory=list)
    retries: int = Field(default=0, ge=0)
    retry_backoff_seconds: float = Field(default=1.0, ge=0, allow_inf_nan=False)

    @field_validator("name", "command")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("dependencies")
    @classmethod
    def valid_dependencies(cls, value: list[str]) -> list[str]:
        if any(not dependency.strip() for dependency in value):
            raise ValueError("dependency names must not be blank")
        return [dependency.strip() for dependency in value]
