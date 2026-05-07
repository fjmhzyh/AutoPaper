from __future__ import annotations

import argparse
import shutil
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
RELEASE_ROOT = PROJECT_ROOT / "release"


def _read_version() -> str:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    project = data.get("project", {}) if isinstance(data, dict) else {}
    version = str(project.get("version", "")).strip()
    if not version:
        raise RuntimeError("pyproject.toml missing project.version")
    return version


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def cmd_version(_args: argparse.Namespace) -> int:
    print(_read_version())
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    version = _read_version()
    platform = str(args.platform).strip().lower()
    if platform not in {"mac", "win"}:
        raise RuntimeError("platform must be mac or win")
    out_dir = RELEASE_ROOT / version / platform
    _ensure_clean_dir(out_dir)
    print(out_dir)
    return 0


def cmd_clean_build(_args: argparse.Namespace) -> int:
    dist_dir = PROJECT_ROOT / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    build_tmp_dir = PROJECT_ROOT / "build" / "tmp"
    if build_tmp_dir.exists():
        shutil.rmtree(build_tmp_dir)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoPaper release helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ver = sub.add_parser("version", help="Print project version")
    p_ver.set_defaults(func=cmd_version)

    p_prep = sub.add_parser("prepare", help="Prepare clean release directory")
    p_prep.add_argument("--platform", required=True, choices=["mac", "win"])
    p_prep.set_defaults(func=cmd_prepare)

    p_clean = sub.add_parser("clean-build", help="Remove local build/dist directories")
    p_clean.set_defaults(func=cmd_clean_build)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"[release] error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
