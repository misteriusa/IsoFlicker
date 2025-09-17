"""CLI utility to ingest preset catalogs into the backend database."""
from __future__ import annotations

import argparse
from pathlib import Path

from backend.core.config import settings
from backend.db.session import configure_engine, create_db_and_tables, get_session
from backend.app.presets_loader import load_preset_catalog, populate_presets


def ingest(preset_path: Path, database_url: str) -> None:
    """Load the preset catalog into the database."""

    configure_engine(database_url)
    create_db_and_tables()
    catalog = load_preset_catalog(preset_path)
    with get_session() as session:
        populate_presets(session, catalog)
        session.commit()


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=settings.preset_file,
        help="Path to the preset JSON catalog",
    )
    parser.add_argument(
        "--database",
        type=str,
        default=settings.database_url,
        help="Database URL (default: %(default)s)",
    )
    return parser


def main() -> None:
    """Run the CLI."""

    args = build_parser().parse_args()
    ingest(args.catalog, args.database)


if __name__ == "__main__":
    main()
