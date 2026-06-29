import hashlib
from pathlib import Path
from typing import Optional


def compute_file_hash(file_path: Path) -> Optional[str]:
    if not file_path.exists():
        return None
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def save_hash(file_path: Path, hash_path: Path) -> None:
    file_hash = compute_file_hash(file_path)
    if file_hash:
        hash_path.write_text(file_hash)


def verify_hash(file_path: Path, hash_path: Path) -> bool:
    if not file_path.exists() or not hash_path.exists():
        return False
    current = compute_file_hash(file_path)
    stored = hash_path.read_text().strip()
    return current == stored


def mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 8:
        return "***"
    return token[:4] + "..." + token[-4:]
