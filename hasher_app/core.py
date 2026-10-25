from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import blake3
except ImportError:
    blake3 = None

CHUNK_SIZE = 64 * 1024


class HasherError(Exception):
    pass


@dataclass
class FileRecord:
    path: str
    sizeBytes: int
    hash: Optional[str]
    error: Optional[str]


@dataclass
class Summary:
    totalFiles: int
    errorFiles: int
    duplicateGroupsCount: int
    totalDuplicateBytes: int


@dataclass
class Report:
    timestamp: str
    rootPath: str
    algorithm: str
    files: List[FileRecord]
    duplicateGroups: List[List[str]]
    summary: Summary


def ensure_algorithm(algorithm: str) -> None:
    if algorithm == "blake3" and blake3 is None:
        raise HasherError("BLAKE3 is not installed. Run: pip install blake3")


def _new_hasher(algorithm: str):
    return sha256() if algorithm == "sha256" else blake3.blake3()


def hash_file(path: Path, algorithm: str) -> str:
    hasher = _new_hasher(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_file(path: Path, algorithm: str, verbose: bool = False) -> FileRecord:
    if verbose:
        print(path, flush=True)
    size = 0
    try:
        size = path.stat().st_size
        return FileRecord(str(path), size, hash_file(path, algorithm), None)
    except OSError as exc:
        return FileRecord(str(path), size, None, f"{type(exc).__name__}: {exc}")


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for directory, dirs, files in os.walk(root, onerror=lambda _: None):
        dirs.sort()
        files.sort()
        for name in files:
            yield Path(directory) / name


def scan(root: Path, algorithm: str, verbose: bool = False) -> List[FileRecord]:
    return [read_file(path, algorithm, verbose) for path in iter_files(root)]


def duplicate_groups(files: List[FileRecord]) -> List[List[FileRecord]]:
    grouped: Dict[str, List[FileRecord]] = {}
    for record in files:
        if record.hash is not None:
            grouped.setdefault(record.hash, []).append(record)
    groups = [
        sorted(records, key=lambda record: record.path)
        for records in grouped.values()
        if len(records) > 1
    ]
    return sorted(groups, key=lambda records: records[0].path)


def build_report(
    root: Path,
    algorithm: str,
    files: List[FileRecord],
    groups: List[List[FileRecord]],
) -> Report:
    return Report(
        timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        rootPath=str(root.resolve()),
        algorithm=algorithm,
        files=files,
        duplicateGroups=[[record.path for record in group] for group in groups],
        summary=Summary(
            totalFiles=len(files),
            errorFiles=sum(record.error is not None for record in files),
            duplicateGroupsCount=len(groups),
            totalDuplicateBytes=sum(
                group[0].sizeBytes * (len(group) - 1) for group in groups
            ),
        ),
    )


def analyze(
    root: Path, algorithm: str, verbose: bool = False
) -> Tuple[Report, List[List[FileRecord]]]:
    ensure_algorithm(algorithm)
    files = scan(root, algorithm, verbose)
    groups = duplicate_groups(files)
    return build_report(root, algorithm, files, groups), groups
