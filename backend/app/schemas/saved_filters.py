from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SavedFilterInput(BaseModel):
    name: str
    keyword: str | None = None
    city: str | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("方案名称不能为空")
        if len(value) > 100:
            raise ValueError("方案名称不能超过 100 个字符")
        return value

    @field_validator("keyword", "city")
    @classmethod
    def clean_condition(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        limit = 200 if info.field_name == "keyword" else 100
        if len(value) > limit:
            raise ValueError(f"{info.field_name} 不能超过 {limit} 个字符")
        return value

    @model_validator(mode="after")
    def require_condition(self):
        if self.keyword is None and self.city is None:
            raise ValueError("关键词和城市不能同时为空")
        return self


class SavedFilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    keyword: str | None
    city: str | None
    created_at: datetime
    updated_at: datetime
