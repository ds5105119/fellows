import json
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBaseConfig(BaseModel):
    db: Annotated[str, Field(serialization_alias="path")]
    host: Annotated[str, Field(serialization_alias="host")]
    port: Annotated[int, Field(serialization_alias="port")]
    user: Annotated[str, Field(default="", serialization_alias="username")]
    password: Annotated[str, Field(default="", serialization_alias="password")]


class JWT(BaseModel):
    algorithm: Annotated[str, Field(default="ES384")]
    access_token_expire_time: Annotated[int, Field(default=3600)]
    refresh_token_expire_time: Annotated[int, Field(default=604800)]


class KeycloakOpenIDClientConfig(BaseModel):
    server_url: str
    client_id: str
    realm_name: str
    client_secret_key: str | None = Field(default=None)


class KeycloakAdminClientConfig(BaseModel):
    server_url: str
    username: str
    password: str
    realm_name: str
    user_realm_name: str
    client_id: str
    client_secret_key: str | None = Field(default=None)
    verify: bool | str

    @field_validator("verify")
    def convert_verify(cls, v):
        if isinstance(v, str):
            lowered = v.lower()
            if lowered == "true":
                return True
            elif lowered == "false":
                return False
        return v


class AWS(BaseModel):
    access_key_id: str
    secret_access_key: str
    storage_bucket_name: str
    s3_region_name: str | None = Field(default=None)
    account_id: str | None = Field(default=None)


class NATS(BaseModel):
    server: str | list[str] = Field(default="nats://localhost:4222")
    name: str | None = Field(default=None)


class ApiAdapter(BaseModel):
    key: str


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent.parent.parent

    debug: Annotated[bool, Field(default=False)]
    base_url: Annotated[str, Field(default="http://localhost:8000")]
    secret_key: Annotated[str, Field(default="YtGHVqSAzFyaHk2OV5XQg3")]

    cors_allow_origin: list[str] = Field(default_factory=list, frozen=True)
    allowed_hosts: list[str] = Field(default_factory=list, frozen=True)

    project_name: Annotated[str, Field(default="API")]
    api_url: Annotated[str, Field(default="/api")]
    swagger_url: Annotated[str, Field(default="/api")]

    jwt: Annotated[JWT, Field(default_factory=JWT)]
    postgres: DataBaseConfig
    wakapi_postgres: DataBaseConfig
    redis: DataBaseConfig
    nats: NATS = Field(default_factory=NATS)

    aws: AWS
    cloudflare: AWS
    keycloak: KeycloakOpenIDClientConfig
    keycloak_admin: KeycloakAdminClientConfig

    open_fiscal_data_api: ApiAdapter
    gov_24_data_api: ApiAdapter
    kakao_api: ApiAdapter
    openai_api: ApiAdapter

    @property
    def postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(scheme="postgresql+asyncpg", **self.postgres.model_dump(by_alias=True))

    @property
    def wakapi_postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(scheme="postgresql+asyncpg", **self.wakapi_postgres.model_dump(by_alias=True))

    @property
    def sync_postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(scheme="postgresql+psycopg", **self.postgres.model_dump(by_alias=True))

    @property
    def redis_dsn(self) -> RedisDsn:
        return RedisDsn.build(scheme="redis", **self.redis.model_dump(by_alias=True))

    model_config = SettingsConfigDict(
        env_file=str(base_dir / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
        env_nested_delimiter="__",
    )


env_json = os.environ.get("FELLOWS_ENV")

if env_json:
    try:
        payload = json.loads(env_json)
    except Exception as e:
        raise RuntimeError(f"ENV에 담긴 JSON 파싱 실패: {e}")
    settings = Settings(**payload)
else:
    settings = Settings()
