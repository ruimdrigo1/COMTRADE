from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_offline(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "offline_cli.py"),
        "--csv",
        args.csv,
        "--line-km",
        str(args.line_km),
        "--kv",
        str(args.kv),
        "--z1",
        str(args.z1),
        "--overcurrent",
        str(args.overcurrent),
        "--overvoltage",
        str(args.overvoltage),
        "--undervoltage",
        str(args.undervoltage),
        "--voltage",
        *args.voltage,
        "--current",
        *args.current,
    ]
    return subprocess.call(cmd)


def run_web() -> int:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(Path(__file__).parent / "app.py"),
    ]
    return subprocess.call(cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runner para VSCode/Windows (modo offline ou web)."
    )
    parser.add_argument(
        "--mode",
        choices=["offline", "web"],
        default="offline",
        help="Modo de execução. Use 'offline' sem internet/dependências externas.",
    )

    parser.add_argument("--csv", default="exemplo.csv", help="CSV de entrada (modo offline)")
    parser.add_argument("--voltage", nargs="+", default=["VA", "VB", "VC"])
    parser.add_argument("--current", nargs="+", default=["IA", "IB", "IC"])
    parser.add_argument("--line-km", type=float, default=120.0)
    parser.add_argument("--kv", type=float, default=230.0)
    parser.add_argument("--z1", type=float, default=0.38)
    parser.add_argument("--overcurrent", type=float, default=500.0)
    parser.add_argument("--overvoltage", type=float, default=1.1)
    parser.add_argument("--undervoltage", type=float, default=0.8)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "web":
        return run_web()

    return run_offline(args)


if __name__ == "__main__":
    raise SystemExit(main())
