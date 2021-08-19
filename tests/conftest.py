import pytest

from s3.s3 import S3Client


@pytest.fixture
async def s3_client():
    client = S3Client(
        access_key='testing',
        secret_key='testing',
        region='ru-central1',
        s3_bucket='test-bucket'
    )
    yield client
    await client.close()
