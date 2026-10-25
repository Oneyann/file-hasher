import json
from dataclasses import asdict
from pathlib import Path
from typing import List, Union

from .core import FileRecord, HasherError, Report


def algorithm_label(algorithm: str) -> str:
    return "SHA-256" if algorithm == "sha256" else "BLAKE3"


def save(report: Report, output: Union[str, Path]) -> Path:
    path = Path(output).expanduser().resolve()
    if path.is_dir():
        raise HasherError(f"Output path is a directory: {path}")
    if not path.parent.is_dir():
        raise HasherError(f"Output directory does not exist: {path.parent}")
    try:
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(asdict(report), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except OSError as exc:
        raise HasherError(
            f"Cannot write report '{path}': {type(exc).__name__}: {exc}"
        )
    return path


def print_hashes(report: Report) -> None:
    print(f"Root: {report.rootPath}")
    print(f"Algorithm: {algorithm_label(report.algorithm)}")
    for record in report.files:
        value = record.hash if record.error is None else f"ERROR: {record.error}"
        print(f"{record.path} | {record.sizeBytes} bytes | {value}")
    print(f"Files: {report.summary.totalFiles} | Errors: {report.summary.errorFiles}")
    if report.summary.duplicateGroupsCount:
        print(f"Duplicate groups: {report.summary.duplicateGroupsCount}")


def print_duplicates(report: Report, groups: List[List[FileRecord]]) -> None:
    print(f"Root: {report.rootPath}")
    print(f"Algorithm: {algorithm_label(report.algorithm)}")
    if not groups:
        print("No duplicates found.")
    else:
        print(f"Duplicate groups: {len(groups)}")
        for index, group in enumerate(groups, 1):
            print(f"Group {index} ({group[0].hash}):")
            for record in group:
                print(f"  {record.path} ({record.sizeBytes} bytes)")
        print(f"Duplicate bytes: {report.summary.totalDuplicateBytes}")
    print(f"Files: {report.summary.totalFiles} | Errors: {report.summary.errorFiles}")


def print_saved(report: Report, path: Path) -> None:
    summary = report.summary
    print(f"Report written to: {path}")
    print(
        f"Files: {summary.totalFiles} | Errors: {summary.errorFiles} | "
        f"Duplicate groups: {summary.duplicateGroupsCount} | "
        f"Duplicate bytes: {summary.totalDuplicateBytes}"
    )
