"""Errors services raise. The API turns them into HTTP responses (see app/main.py)."""


class NotFound(Exception):
    """-> 404"""


class Conflict(Exception):
    """-> 409"""
