from pydantic import BaseModel


class DomainCredential(BaseModel):
    username: str
    password: str
    domain: str


class SecretValue(BaseModel):
    username: str
    password: str
