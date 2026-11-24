"""Checkpointed downloads for reviewed, permitted public sources."""

import hashlib
import http.client
import json
import os
import tempfile
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .market_store import raw_blob, sha256_file


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", encoding="utf-8", delete=False) as temp:
        staging = Path(temp.name)
        try:
            json.dump(data, temp, indent=2, ensure_ascii=False, allow_nan=False)
            temp.write("\n")
            temp.flush()
            os.fsync(temp.fileno())
            staging.replace(path)
        finally:
            staging.unlink(missing_ok=True)


def _retry_delay(header, fallback):
    if not header:
        return fallback
    try:
        return float(int(header))
    except ValueError:
        return max(0, (parsedate_to_datetime(header) - datetime.now(UTC)).total_seconds())


def fetch(root, url, *, refresh=False, max_bytes=128_000_000):
    """Fetch a declared HTTPS object. A partial stream never becomes a checkpoint.

    Only callers with a reviewed source should use this helper. A refresh keeps the
    prior content-addressed blob and retries transient failures within the stated budget.
    """
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("download URL must be credential-free HTTPS")
    root = Path(root)
    key = hashlib.sha256(url.encode()).hexdigest()
    checkpoint = root / "checkpoints" / (key + ".json")
    if checkpoint.is_file() and not refresh:
        existing = json.loads(checkpoint.read_text())
        blob = root / existing["raw_path"]
        if not blob.is_file() or sha256_file(blob) != existing["raw_sha256"]:
            raise ValueError(f"cached source hash mismatch for {url}")
        return blob, existing
    staging = root / "staging"
    staging.mkdir(parents=True, exist_ok=True, mode=0o700)
    attempts = []
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "Foolshot/0.1 research archive validator"})
            with urlopen(request, timeout=25) as response, tempfile.NamedTemporaryFile(dir=staging) as tmp:
                final_url = response.geturl()
                if urlsplit(final_url).hostname != parsed.hostname:
                    raise ValueError(f"download redirected outside the reviewed source host: {final_url}")
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > max_bytes:
                    raise ValueError("source exceeds the configured download size")
                size = 0
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("source exceeds the configured download size")
                    tmp.write(chunk)
                if not size or (length is not None and size != int(length)):
                    raise http.client.IncompleteRead(b"", int(length or 1) - size)
                tmp.flush()
                sha, _, blob = raw_blob(root, tmp.name)
                info = {
                    "url": url, "status": response.status, "raw_sha256": sha,
                    "raw_path": str(blob.relative_to(root)), "raw_bytes": size,
                    "acquired_at": datetime.now(UTC).isoformat(),
                    "last_modified": response.headers.get("Last-Modified"),
                    "etag": response.headers.get("ETag"), "prior_attempts": attempts,
                }
            write_json(checkpoint, info)
            return blob, info
        except (HTTPError, URLError, OSError, http.client.IncompleteRead) as exc:
            attempts.append(str(exc))
            status = exc.code if isinstance(exc, HTTPError) else None
            delay = 2 ** attempt
            if isinstance(exc, HTTPError) and status == 429:
                try:
                    delay = _retry_delay(exc.headers.get("Retry-After"), delay)
                except (TypeError, ValueError, OverflowError):
                    delay = 60
            if attempt == 2 or delay > 30 or (status and status not in (429, 500, 502, 503, 504)):
                write_json(root / "reports" / "download-errors" / (key + ".json"),
                           {"url": url, "attempts": attempts, "status": status})
                raise
            time.sleep(delay)
