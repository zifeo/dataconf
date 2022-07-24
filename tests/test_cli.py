from dataconf.exceptions import ParseException
from dataconf.utils import __cli_parse as cli_parse
import pytest


class TestCli:
    def test_simple(self) -> None:
        assert cli_parse(["--test", "1"]) == dict(test="1")

    def test_with_cmd(self) -> None:
        assert cli_parse(["dataconf", "--test", "1"]) == dict(test="1")

    def test_obj(self) -> None:
        assert cli_parse(["--test--test", "1"]) == dict(test=dict(test="1"))

    def test_ls(self) -> None:
        assert cli_parse(["--test-0", "1", "--test-1", "2"]) == dict(test=["1", "2"])

    def test_nested(self) -> None:
        assert cli_parse(["--A-", "{ name: Test }"]) == dict(a=dict(name="Test"))

    def test_invalid(self) -> None:
        with pytest.raises(ParseException):
            cli_parse(["--a", "1", "--b"])

        with pytest.raises(ParseException):
            cli_parse(["--a"])
