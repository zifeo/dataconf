class TypeConfigException(Exception):
    """Type mismatch exception."""


class MissingTypeException(Exception):
    """Missing type exception (e.g. List instead of List[int]."""


class AmbiguousSubclassException(Exception):
    """Multiple subclasses match the the given parameters. Use '_type' field to disambiguate"""


class MalformedConfigException(Exception):
    """Missing values exception."""


class UnexpectedKeysException(Exception):
    """Unexpected keys exception."""


class EnvListOrderException(Exception):
    """Ordering exception."""


class EnvListFormatException(Exception):
    """Format exception."""


class ParseException(Exception):
    """Parsing exception."""
