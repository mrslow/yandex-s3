# Yandex-S3

Asyncio compatible SDK for Yandex Object Storage inspired by [aioaws](https://github.com/samuelcolvin/aioaws).

This library does not depend on boto, boto3 or any of the other bloated, opaque and mind thumbing AWS SDKs. Instead, it
is written from scratch to provide clean, secure and easily debuggable access to AWS services I want to use.

It currently supports:
* **S3** - list, delete, recursive delete, generating signed upload URLs, generating signed download URLs
* [AWS Signature Version 4](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-auth-using-authorization-header.html)
  authentication for any AWS service (this is the only clean & modern implementation of AWS4 I know of in python, see
  [`core.py`](https://github.com/mrslow/yandex-s3/blob/master/yandex-s3/core.py#L114-L175))

The only dependencies of **yandex-s3**, are:
* **aiofiles** - for asynchronous reading of files
* **cryptography** - for verifying SNS signatures
* **httpx** - for HTTP requests
* **pydantic** - for validating responses

## Install

```bash
pip install yandex-s3
```

## S3 Usage


```py
import asyncio
# requires `pip install yandex-s3`
from s3 import S3Client

# requires `pip install devtools`
from devtools import debug

async def s3_demo():
    s3 = S3Client(
            access_key='<access key>', 
            secret_key='<secret key>', 
            region='<region>', 
            s3_bucket='test-bucket'
    )

    # upload a file:
    await s3.upload('dir/subdir/dummy.txt', b'Dummy')

    # list all files in a bucket
    files = [f async for f in s3.list()]
    debug(files)
    """
    [
        S3File(
            key='dir/subdir/dummy.txt',
            last_modified=datetime.datetime(...),
            size=5,
            e_tag='...',
            storage_class='STANDARD',
        ),
    ] (list) len=1
    """
    # list all files with a given prefix in a bucket
    files = [f async for f in s3.list('dir/subdir/')]
    debug(files)

    # # delete a file
    # await s3.delete('dir/subdir/dummy.txt')
    # # delete two files
    # await s3.delete('dir/subdir/file1.txt', 'dir/subdir/file2.txt')
    # delete recursively based on a prefix
    await s3.delete_recursive('dir/subdir')

    # generate an upload link suitable for sending to a borwser to enabled
    # secure direct file upload (see below)
    upload_data = s3.signed_upload_url(
        path='dir/subdir',
        filename='dummy.txt',
        content_type='text/plain',
        size=123,
    )
    debug(upload_data)
    """
    {
        'url': 'https://test-bucket.storage.yandexcloud.net/',
        'fields': {
            'Key': 'dir/subdir/dummy.txt',
            'Content-Type': 'text/plain',
            'AWSAccessKeyId': '...',
            'Content-Disposition': 'attachment; filename="dummy.txt"',
            'Policy': ('...'),
            'Signature': '...',
        },
    } (dict) len=2
    """

    # generate a temporary link to allow yourself or a client to download a file
    download_url = s3.signed_download_url('dir/subdir/dummy.txt', max_age=60)
    print(download_url)
    #> https://test-bucket.storage.yandexcloud.net/dir/subdir/dummy.txt?AWSAccessKeyId=...&Signature=...&Expires=...
    
    # download file
    content = await s3.download('dir/subdir/dummy.txt')
    print(content)
    #> b'Dummy'
    

async def main():
    await s3_demo()

asyncio.run(main())
```
