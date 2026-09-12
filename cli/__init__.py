"""Command-line parser and command handlers."""

from cli.handlers import dispatch
from cli.parser import build_parser

__all__ = ["build_parser", "dispatch"]
