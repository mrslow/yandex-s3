from typing import Protocol


class BaseConfigProtocol(Protocol):
    access_key: str
    secret_key: str
    region: str


class S3ConfigProtocol(Protocol):
    access_key: str
    secret_key: str
    region: str
    s3_bucket: str
