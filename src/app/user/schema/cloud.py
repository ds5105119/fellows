from pydantic import BaseModel, ConfigDict, Field


class FileRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    algorithm: str = Field(default="AES256")
    key: str
    sse_key: str | None = Field(default=None)


class FileRecordResponseOnly(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    algorithm: str = Field(default="AES256")
    key: str | None = Field(default=None)
    sse_key: str | None = Field(default=None)


class PresignedPutRequest(BaseModel):
    suffix: str


class PresignedPutResponse(BaseModel):
    presigned_url: str
    key: str
    algorithm: str = Field(default="AES256")
    sse_key: str
    md5: str


class PresignedGetRequest(BaseModel):
    algorithm: str = Field(default="AES256")
    key: str
    sse_key: str | None = Field(default=None)
    md5: str | None = Field(default=None)


class PresignedHeader(BaseModel):
    x_amz_server_side_encryption_customer_algorithm: str | None = Field(default=None)
    x_amz_server_side_encryption_customer_key: str | None = Field(default=None)
    x_amz_server_side_encryption_customer_key_MD5: str | None = Field(default=None)
