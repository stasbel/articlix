"""Module for custom exceptions"""

__all__ = ['FetchError']


class _Error(Exception):
    """Base class for all custom exceptions within module"""


class FetchError(_Error):
    """Raise an exception when fetch error occured."""
