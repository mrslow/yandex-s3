import hashlib
import hmac
import logging
from base64 import b64encode
from binascii import hexlify
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional

from httpx import URL, AsyncClient, Response

from ._utils import get_config_attr, utcnow

if TYPE_CHECKING:
    from ._types import BaseConfigProtocol

__all__ = 'YandexS3Client', 'RequestError'
logger = logging.getLogger('s3.core')

_AWS_AUTH_REQUEST = 'aws4_request'
_CONTENT_TYPE = 'application/x-www-form-urlencoded'
_CANONICAL_REQUEST = """\
{method}
{path}
{query}
{canonical_headers}
{signed_headers}
{payload_sha256_hash}"""
_AUTH_ALGORITHM = 'AWS4-HMAC-SHA256'
_CREDENTIAL_SCOPE = '{date_stamp}/{region}/{service}/{auth_request}'
_STRING_TO_SIGN = """\
{algorithm}
{x_amz_date}
{credential_scope}
{canonical_request_hash}"""
_AUTH_HEADER = ('{algorithm} Credential={access_key}/{credential_scope},'
                'SignedHeaders={signed_headers},Signature={signature}')


class YandexS3Client:
    """
    HTTP client for Yandex Object Storage with authentication
    """

    def __init__(self, config: 'BaseConfigProtocol'):
        self.client = AsyncClient(timeout=30)
        self.access_key = get_config_attr(config, 'access_key')
        self.secret_key = get_config_attr(config, 'secret_key')
        self.region = get_config_attr(config, 'region')
        bucket = get_config_attr(config, 's3_bucket')
        self.host = f'{bucket}.storage.yandexcloud.net'
        self.service = 's3'
        self.endpoint = f'https://{self.host}'

    async def get(
            self,
            path: str = '',
            *,
            params: Optional[Dict[str, Any]] = None
    ) -> Response:
        return await self.request('GET', path=path, params=params)

    async def raw_post(
            self,
            url: str,
            *,
            expected_status: int,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, str]] = None,
            files: Optional[Dict[str, bytes]] = None,
    ) -> Response:
        r = await self.client.post(url, params=params, data=data, files=files)
        if r.status_code == expected_status:
            return r
        else:
            raise RequestError(r)

    async def post(
            self,
            path: str = '',
            *,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[bytes] = None,
            content_type: Optional[str] = None,
    ) -> Response:
        return await self.request('POST',
                                  path=path,
                                  params=params,
                                  data=data,
                                  content_type=content_type)

    async def request(
            self,
            method: Literal['GET', 'POST'],
            *,
            path: str,
            params: Optional[Dict[str, Any]],
            data: Optional[bytes] = None,
            content_type: Optional[str] = None,
    ) -> Response:
        url = URL(f'{self.endpoint}{path}',
                  params=[(k, v) for k, v in sorted((params or {}).items())])
        auth_headers = self._auth_headers(method,
                                          url,
                                          data=data,
                                          content_type=content_type)
        r = await self.client.request(method,
                                      url,
                                      content=data,  # type: ignore
                                      headers=auth_headers,)
        if r.status_code != 200:
            raise RequestError(r)
        return r

    def _auth_headers(
            self,
            method: Literal['GET', 'POST'],
            url: URL,
            *,
            data: Optional[bytes] = None,
            content_type: Optional[str] = None,
    ) -> Dict[str, str]:
        n = utcnow()
        x_amz_date = n.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = n.strftime('%Y%m%d')
        data = data or b''
        content_type = content_type or _CONTENT_TYPE

        # WARNING!
        # order is important here, headers need to be in alphabetical order
        payload_sha256_hash = hashlib.sha256(data).hexdigest()

        headers = {
            'content-md5': b64encode(hashlib.md5(data).digest()).decode(),
            'content-type': content_type,
            'host': self.host,
            'x-amz-content-sha256': payload_sha256_hash,
            'x-amz-date': x_amz_date,
        }

        ctx = dict(
            method=method,
            path=url.path,
            query=url.query.decode(),
            access_key=self.access_key,
            algorithm=_AUTH_ALGORITHM,
            x_amz_date=x_amz_date,
            auth_request=_AWS_AUTH_REQUEST,
            date_stamp=date_stamp,
            payload_sha256_hash=payload_sha256_hash,
            region=self.region,
            service=self.service,
            signed_headers=';'.join(headers),
        )
        ctx.update(credential_scope=_CREDENTIAL_SCOPE.format(**ctx))
        canonical_headers = ''.join(f'{k}:{v}\n' for k, v in headers.items())

        canonical_request = _CANONICAL_REQUEST.format(
            canonical_headers=canonical_headers, **ctx).encode()

        s2s = _STRING_TO_SIGN.format(canonical_request_hash=hashlib.sha256(
            canonical_request).hexdigest(), **ctx)

        key_parts = (
            b'AWS4' + self.secret_key.encode(),
            date_stamp,
            self.region,
            self.service,
            _AWS_AUTH_REQUEST,
            s2s,
        )
        signature: bytes = reduce(_reduce_signature, key_parts)  # type: ignore

        authorization_header = _AUTH_HEADER.format(
            signature=hexlify(signature).decode(), **ctx)
        headers.update({'authorization': authorization_header})
        return headers


def _reduce_signature(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


class RequestError(RuntimeError):
    def __init__(self, r: Response):
        error_msg = (f'unexpected response from {r.request.method} '
                     f'"{r.request.url}": {r.status_code}')
        super().__init__(error_msg)
        self.response = r
        self.status = r.status_code

    def __str__(self) -> str:
        return f'{self.args[0]}, response:\n{self.response.text}'
