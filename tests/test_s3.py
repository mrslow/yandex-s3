import pytest

from datetime import datetime
from uuid import uuid4

from s3.core import RequestError

base_url = 'https://test-bucket.storage.yandexcloud.net'

list_data = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n'
    b'  <Name>flk-test-bucket</Name>\n'
    b'  <Prefix></Prefix>\n'
    b'  <MaxKeys>1000</MaxKeys>\n'
    b'  <IsTruncated>false</IsTruncated>\n'
    b'  <EncodingType>url</EncodingType>\n'
    b'  <Contents>\n'
    b'    <Key>dir/subdir/dummy.txt</Key>\n'
    b'    <LastModified>2021-08-19T08:39:21.409Z</LastModified>\n'
    b'    <Owner>\n'
    b'      <ID>ajef9a0uck81dkvnc8jf</ID>\n'
    b'      <DisplayName>ajef9a0uck81dkvnc8jf</DisplayName>\n'
    b'    </Owner>\n'
    b'    <ETag>&#34;bcf036b6f33e182d4705f4f5b1af13ac&#34;</ETag>\n'
    b'    <Size>5</Size>\n'
    b'    <StorageClass>STANDARD</StorageClass>\n'
    b'  </Contents>\n'
    b'  <Marker></Marker>\n'
    b'</ListBucketResult>\n'
)

delete_data = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<DeleteResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n'
    b'  <Deleted>\n'
    b'    <Key>dir/subdir/dummy.txt</Key>\n'
    b'    <VersionId>null</VersionId>\n'
    b'  </Deleted>\n'
    b'</DeleteResult>'
)

get_data = b'Dummy'

base_headers = {
    'Server': 'nginx',
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=60',
}

upload_headers = {
    'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'Transfer-Encoding': 'chunked',
    'Etag': f'"{uuid4().hex}"',
    'X-Amz-Request-Id': uuid4().hex[:16],
    'X-Amz-Version-Id': None
}.update(base_headers)

list_headers = {
    'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'Content-Type': 'application/xml; charset=UTF-8',
    'Content-Length': len(list_data),
    'X-Amz-Request-Id': uuid4().hex[:16],
}.update(base_headers)

delete_headers = {
    'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'Content-Type': 'application/xml; charset=UTF-8',
    'Content-Length': len(delete_data),
    'X-Amz-Request-Id': uuid4().hex[:16],
}.update(base_headers)

get_headers = {
    'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'Content-Type': 'application/octet-stream',
    'Content-Length': f'{len(get_data)}',
    'Accept-Ranges': 'bytes',
    'Etag': f'"{uuid4().hex}"',
    'Last-Modified': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'X-Amz-Request-Id': uuid4().hex[:16],
    'X-Amz-Version-Id': None
}.update(base_headers)


@pytest.mark.asyncio
async def test_upload_object(s3_client, httpx_mock):
    httpx_mock.add_response(
        url=base_url,
        method='POST',
        status_code=204,
        headers=upload_headers,
        data=b'')

    try:
        await s3_client.upload('dummy.txt', b'Dummy')
    except RequestError as exc:
        pytest.fail(exc)


@ pytest.mark.asyncio
async def test_download_object(s3_client, httpx_mock):
    httpx_mock.add_response(
        url=s3_client.signed_download_url('dir/subdir/dummy.txt'),
        method='GET',
        status_code=200,
        headers=get_headers,
        data=get_data)

    r = await s3_client.download('dir/subdir/dummy.txt')
    assert r == b'Dummy'


@pytest.mark.asyncio
async def test_list_objects(s3_client, httpx_mock):
    httpx_mock.add_response(
        url=f'{base_url}?list-type=2&prefix=dir/subdir&continuation-token=',
        method='GET',
        status_code=200,
        headers=list_headers,
        data=list_data)

    objects = [elem async for elem in s3_client.list(prefix='dir/subdir')]
    assert len(objects) == 1
    assert objects[0].key == 'dir/subdir/dummy.txt'


@pytest.mark.asyncio
async def test_delete_objects(s3_client, httpx_mock):
    httpx_mock.add_response(
        url=f'{base_url}?delete=1',
        method='POST',
        status_code=200,
        headers=delete_headers,
        data=delete_data)

    obj = await s3_client.delete('dir/subdir/dummy.txt')
    assert len(obj) == 1
    assert obj[0] == 'dir/subdir/dummy.txt'
