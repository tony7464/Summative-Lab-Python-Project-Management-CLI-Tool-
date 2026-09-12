#!/usr/bin/env python3
"""Entry point for the project-management CLI."""

import logging
import sys

from cli.handlers import dispatch
from cli.parser import build_parser
from services.storage_service import StorageService
from utils.errors import PersistenceError
from utils.formatters import print_error


def main(argv=None):
    """Parse arguments, load persisted data, and run the requested command.

    Args:
        argv: Optional argument list used by tests. Defaults to sys.argv[1:].

    Returns:
        int: Process exit code.
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    storage = StorageService()
    try:
        storage.load()
    except PersistenceError as exc:
        print_error(str(exc))
        return 1
    return dispatch(args, storage)


if __name__ == "__main__":
    sys.exit(main())
