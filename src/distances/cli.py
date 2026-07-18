import argparse
from pathlib import Path

from distances.matrix import build_distance_matrix
from distances.settings import OUTPUTS_DIR


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="distances",
        description="Generate origin-destination distance matrices using a local OSRM server.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    matrix = sub.add_parser(
        "matrix", help="Generate the origin-destination distance matrix"
    )
    matrix.add_argument(
        "--settings",
        type=Path,
        default=None,
        help="Path to settings.yaml (defaults to config/settings.yaml)",
    )
    matrix.add_argument(
        "--output",
        type=Path,
        default=OUTPUTS_DIR / "distance_matrix.xlsx",
        help="Path of the output Excel file",
    )

    args = parser.parse_args(argv)

    if args.command == "matrix":
        results = build_distance_matrix(settings_path=args.settings)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        results.to_excel(args.output, index=False)
        print(f"pairs: {len(results)}")
        print(f"saved: {args.output}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
