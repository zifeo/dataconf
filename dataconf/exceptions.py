class TypeConfigException(Exception):
    """Type mismatch exception."""

    pass


class MissingTypeException(Exception):
    """Missing type exception (e.g. List instead of List[int]."""

    pass


class MalformedConfigException(Exception):
    """Missing values exception."""

    pass


class UnexpectedKeysException(Exception):
    """Unexpected keys exception."""

    pass


class EnvListOrderException(Exception):
    """Ordering exception."""

    pass


class ParseException(Exception):
    """Parsing exception."""

    pass
