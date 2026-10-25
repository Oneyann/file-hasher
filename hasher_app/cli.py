import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from .core import HasherError, analyze, ensure_algorithm, read_file
from .report import (
    algorithm_label,
    print_duplicates,
    print_hashes,
    print_saved,
    save,
)

DEFAULT_REPORT = "hasher_report.json"


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise HasherError(f"Path does not exist: {path}")
    return path.resolve()


def _file(value: str) -> Path:
    path = _resolve(value)
    if not path.is_file():
        raise HasherError(f"Not a file: {path}")
    return path


def _directory(value: str) -> Path:
    path = _resolve(value)
    if not path.is_dir():
        raise HasherError(f"Not a directory: {path}")
    return path


def _root(value: str) -> Path:
    path = _resolve(value)
    if not (path.is_file() or path.is_dir()):
        raise HasherError(f"Not a file or directory: {path}")
    return path


def _run_scan(
    args: argparse.Namespace,
    *,
    directory: bool = False,
    duplicates: bool = False,
    default_output: Optional[Path] = None,
) -> int:
    root = _directory(args.path) if directory else _root(args.path)
    report, groups = analyze(root, args.algorithm, args.verbose)
    output = args.output if args.output is not None else default_output
    if output is not None:
        print_saved(report, save(report, output))
    elif duplicates:
        print_duplicates(report, groups)
    else:
        print_hashes(report)
    return 0


def run_hash(args: argparse.Namespace) -> int:
    return _run_scan(args)


def run_find_duplicates(args: argparse.Namespace) -> int:
    return _run_scan(args, directory=True, duplicates=True)


def run_report(args: argparse.Namespace) -> int:
    return _run_scan(args, default_output=Path.cwd() / DEFAULT_REPORT)


def _compare_paths(args: argparse.Namespace) -> Tuple[str, str]:
    if args.path and (args.path1 or args.path2):
        raise HasherError("Use either --path FILE1 FILE2 or -p1 FILE1 -p2 FILE2")
    if args.path:
        return args.path[0], args.path[1]
    if args.path1 and args.path2:
        return args.path1, args.path2
    raise HasherError("compare requires two file paths")


def run_compare(args: argparse.Namespace) -> int:
    raw_paths = _compare_paths(args)
    paths = [_file(value) for value in raw_paths]
    ensure_algorithm(args.algorithm)
    records = [read_file(path, args.algorithm, args.verbose) for path in paths]
    for record in records:
        if record.error:
            raise HasherError(f"Cannot hash '{record.path}': {record.error}")
    print(f"Algorithm: {algorithm_label(args.algorithm)}")
    for index, record in enumerate(records, 1):
        print(f"File {index}: {record.path}")
        print(f"  Size: {record.sizeBytes} bytes")
        print(f"  Hash: {record.hash}")
    if records[0].hash == records[1].hash:
        print("Result: MATCH (hashes are identical)")
    else:
        print("Result: MISMATCH (hashes do not match)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="hasher.py",
        description="Hash files and directories, compare files, find duplicates.",
    )
    commands = parser.add_subparsers(dest="command", title="commands", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-a",
        "--algorithm",
        choices=("sha256", "blake3"),
        default="sha256",
        help="hash algorithm (default: %(default)s)",
    )
    common.add_argument(
        "--verbose",
        action="store_true",
        help="print each file path while it is being processed",
    )

    scan = argparse.ArgumentParser(add_help=False)
    scan.add_argument("-p", "--path", required=True, metavar="PATH")
    scan.add_argument("-o", "--output", metavar="FILE")

    commands.add_parser(
        "hash",
        parents=[common, scan],
        help="hash a file or all files in a directory",
        description="Compute a hash for a file or recursively for a directory.",
    )
    commands.add_parser(
        "find-duplicates",
        parents=[common, scan],
        help="find files with identical hashes in a directory",
        description="Recursively find duplicate files by hash in a directory.",
    )
    commands.add_parser(
        "report",
        parents=[common, scan],
        help="scan a path and always write a JSON report",
        description=(
            "Scan a path and write a JSON report. "
            f"Without -o, the report is saved as {DEFAULT_REPORT}."
        ),
    )

    compare = commands.add_parser(
        "compare",
        parents=[common],
        help="compare two files by their hashes",
        description=(
            "Compare two files by hash. Use --path FILE1 FILE2 "
            "or -p1 FILE1 -p2 FILE2."
        ),
    )
    compare.add_argument(
        "-p",
        "--path",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="two files to compare",
    )
    compare.add_argument("-p1", "--path1", metavar="FILE")
    compare.add_argument("-p2", "--path2", metavar="FILE")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    commands = {
        "hash": run_hash,
        "compare": run_compare,
        "find-duplicates": run_find_duplicates,
        "report": run_report,
    }
    try:
        return commands[args.command](args)
    except HasherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 1
