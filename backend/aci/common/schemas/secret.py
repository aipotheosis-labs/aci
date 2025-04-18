from pydantic import BaseModel


class SecretCreate(BaseModel):
    key: str
    value: bytes


class SecretUpdate(BaseModel):
    value: bytes
