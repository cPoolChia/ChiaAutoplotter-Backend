from __future__ import annotations

from typing import IO, Any
import hashlib

BUF_SIZE = 65536


def get_file_hash(
    file: IO[Any], *, hash_obj: hashlib._Hash = hashlib.md5()
) -> hashlib._Hash:
    while True:
        data = file.read(BUF_SIZE)
        if not data:
            file.seek(0)
            return hash_obj
        hash_obj.update(data)
