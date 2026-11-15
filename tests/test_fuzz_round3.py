import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from datetime import time
from pathlib import Path
from typing import Final

import pytest
from pyhocon import ConfigFactory
from pytest_httpserver import HTTPServer

import dataconf
from dataconf import dumps
from dataconf import loads
from dataconf.exceptions import ParseException
from dataconf.exceptions import TypeConfigException
from dataconf.exceptions import UnexpectedKeysException
from dataconf.main import parse
from dataconf.utils import __cli_parse as cli_parse
from dataconf.utils import __env_vars_parse as env_parse
from tests.conftest import file_handler
from tests.test_parse import InputType
from tests.test_parse import StringImpl


class TestFuzzRound3:
    def test_mapping_annotation(self) -> None:
        @dataclass
        class A:
            m: Mapping[str, int]

        assert dataconf.dict({"m": {"a": 1}}, A) == A(m={"a": 1})

    def test_default_factory_dataclass_list(self) -> None:
        @dataclass
        class Nested:
            a: int = 1

        @dataclass
        class A:
            xs: list[Nested] = field(default_factory=lambda: [Nested()])

        assert dataconf.dict({}, A) == A(xs=[Nested()])

    def test_type_does_not_mutate_config(self) -> None:
        conf = ConfigFactory.from_dict(
            {"_type": "StringImpl", "name": "ada", "age": "1"}
        )
        got = parse(conf, InputType)
        assert got == StringImpl(name="ada", age="1")
        assert conf["_type"] == "StringImpl"

    def test_time_value(self) -> None:
        @dataclass
        class A:
            t: time

        assert dataconf.dict({"t": time(1, 2, 3)}, A) == A(t=time(1, 2, 3))
        assert loads('t = "01:02:03"', A) == A(t=time(1, 2, 3))

    def test_ignore_unexpected_does_not_flip_union(self) -> None:
        @dataclass
        class A:
            x: int

        @dataclass
        class B:
            x: int
            y: str

        @dataclass
        class C:
            v: A | B

        assert dataconf.dict({"v": {"x": 1, "y": "z"}}, C, ignore_unexpected=True) == C(
            v=B(x=1, y="z")
        )

    def test_bool_str_union_keeps_string(self) -> None:
        @dataclass
        class A:
            v: bool | str

        assert dataconf.dict({"v": "true"}, A) == A(v="true")
        assert dataconf.dict({"v": True}, A) == A(v=True)

    def test_empty_mapping_is_not_a_list(self) -> None:
        @dataclass
        class A:
            xs: list[str]

        with pytest.raises(TypeConfigException):
            dataconf.dict({"xs": {}}, A)

    def test_final_int(self) -> None:
        @dataclass
        class A:
            x: Final[int]

        assert dataconf.dict({"x": 3}, A) == A(x=3)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695")
    def test_pep695_alias(self) -> None:
        from typing import TypeAliasType

        UserId = TypeAliasType("UserId", int)

        @dataclass
        class A:
            u: UserId

        assert dataconf.dict({"u": 7}, A).u == 7

    def test_env_scalar_then_index(self) -> None:
        with pytest.raises(ParseException):
            env_parse("P", {"P_A": "hello", "P_A_0": "world"})

    def test_empty_env_and_cli_key(self) -> None:
        with pytest.raises(ParseException, match="empty"):
            env_parse("EMP", {"EMP_": "{}"})
        with pytest.raises(ParseException, match="empty"):
            cli_parse(["--", "x"])

    def test_env_int_dict_keys_are_strings(self) -> None:
        assert env_parse("P", {"P_0": "1"}) == {"0": "1"}

    def test_env_leading_zeros_and_unicode_digits(self) -> None:
        assert env_parse("P", {"P_A_01": "x"}) == {"a_01": "x"}
        assert env_parse("P", {"P_A_\u0661": "x"}) == {"a_\u0661": "x"}

    def test_env_missing_substitution_is_parse_exception(self) -> None:
        with pytest.raises(ParseException):
            env_parse("P", {"P_NESTED_": "${MISSING_DATACONF_VAR}"})

    def test_yaml_non_str_keys(self) -> None:
        @dataclass
        class A:
            m: dict[str, int]

        assert loads("m:\n  1: 2\n", A, loader=dataconf.YAML) == A(m={"1": 2})
        assert loads("m:\n  true: 2\n", A, loader=dataconf.YAML) == A(m={"True": 2})

    def test_json_unicode_escape(self) -> None:
        @dataclass
        class A:
            s: str

        assert loads('{"s": "\\u00e9"}', A) == A(s="é")

    def test_yaml_and_toml_errors_are_parse_exception(self) -> None:
        @dataclass
        class A:
            s: str

        with pytest.raises(ParseException):
            loads(":\n:", A, loader=dataconf.YAML)
        with pytest.raises(ParseException):
            loads("s = [", A, loader=dataconf.TOML)

    def test_url_trailing_slash_yaml(self, httpserver: HTTPServer) -> None:
        @dataclass
        class A:
            hello: str
            foo: list[str]

        httpserver.expect_request("/simple.yaml/").respond_with_handler(
            file_handler("confs/simple.yaml")
        )
        got = dataconf.url(httpserver.url_for("/simple.yaml/"), A)
        assert got == A(hello="bonjour", foo=["bar"])

    def test_file_url_query_rejected(self) -> None:
        @dataclass
        class A:
            hello: str

        with pytest.raises(ParseException, match="query"):
            dataconf.url("file:///tmp/missing.yaml?x=1", A)

    def test_bytes_dump_roundtrip(self) -> None:
        @dataclass
        class A:
            raw: bytes

        original = A(raw=b"hi")
        text = dumps(original, out="json")
        assert loads(text, A) == original

    def test_dotted_dict_keys_dump(self) -> None:
        @dataclass
        class A:
            m: dict[str, int]

        original = A(m={"a.b": 1})
        text = dumps(original, out="json")
        assert json.loads(text) == {"m": {"a.b": 1}}
        hocon = dumps(original, out="hocon")
        assert "a.b" in hocon
        dumps(original, out="yaml")
        with pytest.raises(ParseException, match="cannot encode dict keys"):
            dumps(original, out="properties")

    def test_init_false_not_dumped(self) -> None:
        @dataclass
        class A:
            a: str
            b: int = field(init=False, default=9)

        text = dumps(A(a="x"), out="hocon")
        assert "b" not in text
        assert loads(text, A) == A(a="x")

    def test_toml_none_dict_value_raises(self) -> None:
        @dataclass
        class A:
            m: dict[str, str | None]

        with pytest.raises(ParseException, match="null dict values"):
            dumps(A(m={"a": None}), out="toml")

    def test_properties_quotes_and_empty_list(self) -> None:
        @dataclass
        class A:
            p: Path
            xs: list[str]
            s: str

        text = dumps(
            A(p=Path("/tmp/\tx"), xs=[], s="a=b"),
            out="properties",
        )
        assert 's = "a=b"' in text
        assert "xs = []" in text
        with pytest.raises(ParseException, match="null list items"):
            dumps(A(p=Path("x"), xs=["a", None], s="s"), out="properties")  # type: ignore[list-item]

    def test_parse_does_not_leave_type_error_from_subclasses(self) -> None:
        @dataclass
        class A:
            extra: str

        with pytest.raises(UnexpectedKeysException):
            dataconf.dict({"extra": "x", "nope": 1}, A)
