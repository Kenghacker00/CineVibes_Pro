import os
import requests
from typing import Optional


def _cfg():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    bucket = os.getenv('SUPABASE_BUCKET', 'profile-pics')
    return url, key, bucket


def is_enabled() -> bool:
    url, key, bucket = _cfg()
    return bool(url and key and bucket)


def _headers(key: str, content_type: Optional[str] = None):
    h = {
        'Authorization': f'Bearer {key}',
        'apikey': key,
    }
    if content_type:
        h['Content-Type'] = content_type
    # allow upserts on upload
    h['x-upsert'] = 'true'
    return h


def upload_bytes(path: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
    """
    Upload bytes to Supabase Storage at given path inside the configured bucket.
    Returns the public URL. Requires the bucket to be public or signed URLs (not handled here).
    """
    url, key, bucket = _cfg()
    if not (url and key and bucket):
        raise RuntimeError('Supabase storage not configured')
    endpoint = f"{url.rstrip('/')}/storage/v1/object/{bucket}/{path.lstrip('/')}"
    resp = requests.put(endpoint, headers=_headers(key, content_type), data=data, timeout=30)
    # 200/201/204 are OK for upsert/put
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(f"Supabase upload failed: {resp.status_code} {resp.text[:200]}")
    return public_url(path)


def delete_object(path: str) -> bool:
    url, key, bucket = _cfg()
    if not (url and key and bucket):
        return False
    endpoint = f"{url.rstrip('/')}/storage/v1/object/{bucket}/{path.lstrip('/')}"
    resp = requests.delete(endpoint, headers=_headers(key), timeout=30)
    return resp.status_code in (200, 204)


def public_url(path: str) -> str:
    url, _key, bucket = _cfg()
    return f"{url.rstrip('/')}/storage/v1/object/public/{bucket}/{path.lstrip('/')}"
