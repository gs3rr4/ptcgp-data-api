"""Summarize card data counts.

Usage:
    python scripts/summary.py --help
"""

import argparse
from ptcgp_api import data


def main() -> None:
    """Print the number of cards and sets available."""
    parser = argparse.ArgumentParser(description="Show data counts")
    parser.parse_args()
    print(f"Cards: {len(data._cards)}")
    print(f"Sets: {len(data._sets)}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
