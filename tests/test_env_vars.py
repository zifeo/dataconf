from dataconf.exceptions import EnvListFormatException, EnvListOrderException
from dataconf.exceptions import ParseException
from dataconf.utils import __env_vars_parse as env_vars_parse
import pytest


class TestEnvVars:
    def test_simple(self) -> None:
        env = {"P_TEST": "1"}
        assert env_vars_parse("P", env) == dict(test="1")
        assert env_vars_parse("P_", env) == dict(test="1")

    def test_no_prefix(self) -> None:
        env = {"TEST": "1"}
        assert env_vars_parse("", env) == dict(test="1")

    def test_double(self) -> None:
        env = {
            "P_TEST": "1",
            "P_TESTA": "2",
        }
        assert env_vars_parse("P", env) == dict(test="1", testa="2")

    def test_obj(self) -> None:
        env = {
            "P_TEST__A__B": "1",
            "P_TEST__A__C": "2",
            "P_TEST__D": "3",
            "P_TEST__E_0": "4",
        }
        assert env_vars_parse("P", env) == dict(
            test=dict(a=dict(b="1", c="2"), d="3", e=["4"])
        )

    def test_ls(self) -> None:
        env = {
            "P_A_0": "1",
            "P_B_0_0": "2",
            "P_C_0_0__C": "3",
            "P_A_1": "4",
        }
        assert env_vars_parse("P", env) == dict(
            a=["1", "4"], b=[["2"]], c=[[dict(c="3")]]
        )

    def test_ls_order(self) -> None:
        env = {
            "P_A_0": "1",
            "P_A_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            env_vars_parse("P", env)

        env = {
            "P_B_0_0": "1",
            "P_B_0_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            env_vars_parse("P", env)

        env = {
            "P_A__B_0": "1",
            "P_A__B_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            env_vars_parse("P", env)

    def test_ls_obj(self) -> None:
        env = {
            "P_A_0__A": "1",
            "P_A_1__A": "2",
        }
        assert env_vars_parse("P", env) == dict(a=[dict(a="1"), dict(a="2")])

        env = {
            "P_A_0__A": "1",
            "P_A_0__B": "2",
        }
        assert env_vars_parse("P", env) == dict(a=[dict(a="1", b="2")])

        env = {
            "P_A_0__A": "1",
            "P_A_0__B": "2",
            "P_A_1__A": "3",
            "P_A_1__B": "4",
        }
        assert env_vars_parse("P", env) == dict(
            a=[dict(a="1", b="2"), dict(a="3", b="4")]
        )

    def test_ls_wrong_obj(self) -> None:
        env = {
            "P_A_0_A": "1",
            "P_A_1_A": "2",
        }
        with pytest.raises(EnvListFormatException):
            env_vars_parse("P", env)

    def test_number(self) -> None:
        env = {
            "A": "1",
            "A_80": "2",
            "A_80_B": "3",
            "A_80_B_1": "4",
        }
        assert env_vars_parse("", env) == dict(
            a="1", a_80="2", a_80_b="3", a_80_b_1="4"
        )

    def test_obj_composed(self) -> None:
        env = {
            "P_A_A__B": "1",
            "P_A_A__B_B": "2",
        }
        assert env_vars_parse("P", env) == dict(a_a=dict(b="1", b_b="2"))

    def test_nested(self) -> None:
        env = {
            "P_A_": "{ name: Test }",
            "P_B_": "d: 1\nc: 2",
            "P_C": "{ name: Test }",
        }
        assert env_vars_parse("P", env) == dict(
            a=dict(name="Test"), b=dict(d=1, c=2), c="{ name: Test }"
        )

    def test_bad_nested_config(self) -> None:
        env = {
            "P_A_0_": "::",
        }
        with pytest.raises(ParseException):
            env_vars_parse("P", env)
