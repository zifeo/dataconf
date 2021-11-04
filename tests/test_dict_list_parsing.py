from dataconf.exceptions import EnvListOrderException
from dataconf.exceptions import EnvParseException
from dataconf.utils import __dict_list_parsing as dict_list_parsing
import pytest


class TestEnvDictParsing:
    def test_simple(self) -> None:
        env = {"P_TEST": "1"}
        assert dict_list_parsing("P", env) == dict(test="1")
        assert dict_list_parsing("P_", env) == dict(test="1")

    def test_double(self) -> None:
        env = {
            "P_TEST": "1",
            "P_TESTA": "2",
        }
        assert dict_list_parsing("P", env) == dict(test="1", testa="2")

    def test_obj(self) -> None:
        env = {
            "P_TEST__A__B": "1",
            "P_TEST__A__C": "2",
            "P_TEST__D": "3",
            "P_TEST__E_0": "4",
        }
        assert dict_list_parsing("P", env) == dict(
            test=dict(a=dict(b="1", c="2"), d="3", e=["4"])
        )

    def test_ls(self) -> None:
        env = {
            "P_A_0": "1",
            "P_B_0_0": "2",
            "P_C_0_0__C": "3",
            "P_A_1": "4",
        }
        assert dict_list_parsing("P", env) == dict(
            a=["1", "4"], b=[["2"]], c=[[dict(c="3")]]
        )

    def test_ls_order(self) -> None:
        env = {
            "P_A_0": "1",
            "P_A_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            dict_list_parsing("P", env)

        env = {
            "P_B_0_0": "1",
            "P_B_0_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            dict_list_parsing("P", env)

        env = {
            "P_A__B_0": "1",
            "P_A__B_2": "2",
        }
        with pytest.raises(EnvListOrderException):
            dict_list_parsing("P", env)

    def test_obj_composed(self) -> None:
        env = {
            "P_A_A__B": "1",
            "P_A_A__B_B": "2",
        }
        assert dict_list_parsing("P", env) == dict(a_a=dict(b="1", b_b="2"))

    def test_nested(self) -> None:
        env = {
            "P_A_": "{ name: Test }",
            "P_B_": "d: 1\nc: 2",
            "P_C": "{ name: Test }",
        }
        assert dict_list_parsing("P", env) == dict(
            a=dict(name="Test"), b=dict(d=1, c=2), c="{ name: Test }"
        )

    def test_bad_nested_config(self) -> None:
        env = {
            "P_A_0_": "::",
        }
        with pytest.raises(EnvParseException):
            dict_list_parsing("P", env)
