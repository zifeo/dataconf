from abc import ABCMeta
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
import os
import tempfile
from typing import Dict
from typing import List
from typing import Optional
from typing import Text
from typing import Union
import pytest

import dataconf
from dataconf.exceptions import TypeConfigException
from dateutil.relativedelta import relativedelta

from dataconf.version import PY310up

PARENT_DIR = os.path.normpath(
    os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir
)


class TestParser:
    def test_readme(self) -> None:
        class AbstractBaseClass:
            pass

        @dataclass
        class Person(AbstractBaseClass):
            name: Text

        @dataclass
        class Zone(AbstractBaseClass):
            area_code: int

        @dataclass
        class Nested:
            a: Text
            b: float

        @dataclass
        class Config:
            str_name: Text
            dash_to_underscore: bool
            float_num: float
            iso_datetime: datetime
            iso_duration: timedelta
            list_data: List[Text]
            nested: Nested
            nested_list: List[Nested]
            duration: relativedelta
            union: Union[Text, int]
            people: AbstractBaseClass
            zone: AbstractBaseClass
            default: Text = "hello"
            default_factory: Dict[Text, Text] = field(default_factory=dict)

        # print(loads(conf, Config))
        assert dataconf.load(
            os.path.join(PARENT_DIR, "confs", "readme.hocon"), Config
        ) == Config(
            str_name=os.environ.get("HOME", "test"),
            dash_to_underscore=True,
            float_num=2.2,
            iso_datetime=datetime(2000, 1, 1, 20),
            iso_duration=timedelta(days=123, hours=4, minutes=5, seconds=6),
            list_data=["a", "b"],
            nested=Nested(a="test", b=1),
            nested_list=[Nested(a="test1", b=2.5)],
            duration=relativedelta(seconds=+2),
            union=1,
            people=Person(name="Thailand"),
            zone=Zone(area_code=42),
            default="hello",
            default_factory={},
        )

    def test_name_conflict_19(self) -> None:
        class P(metaclass=ABCMeta):
            pass

        @dataclass
        class A(P):
            file_path: Text
            sep: Text = ","

        @dataclass
        class B(P):
            file_path: Text
            engine: Text

        @dataclass
        class C:
            name: Text
            data: P
            training: Optional[bool] = False

        conf = """
        {
            name: Countries Model Parquet Version 1.0.2
            data {
                file_path: "../data/countries.parquet"
                engine: auto
            }
        }
        """

        assert dataconf.loads(conf, C) == C(
            name="Countries Model Parquet Version 1.0.2",
            data=B(file_path="../data/countries.parquet", engine="auto"),
            training=False,
        )

        conf = """
        {
            name: Countries Model CSV Version 1.0.2
            data {
                file_path: "../data/countries_data.csv"
                sep: ";"
            }
            training: true
        }
        """

        assert dataconf.loads(conf, C) == C(
            name="Countries Model CSV Version 1.0.2",
            data=A(file_path="../data/countries_data.csv", sep=";"),
            training=True,
        )

    def test_dash_to_underscore_20(self) -> None:
        @dataclass
        class A:
            a_a: bool

        conf = """
        a-a = false
        """
        assert dataconf.loads(conf, A) == A(a_a=False)

    def test_url(self) -> None:
        @dataclass
        class A:
            url: str

        os.environ["P_URL"] = "https://github.com/zifeo/dataconf"
        assert dataconf.env("P", A) == A(url="https://github.com/zifeo/dataconf")
        os.environ.pop("P_URL")

    def test_env_var_cast_35(self) -> None:
        @dataclass
        class Example:
            hello: Optional[str]
            world: str
            float_num: float
            int_num: int
            bool_var: bool

        os.environ["DC_WORLD"] = "monde"
        os.environ["DC_FLOAT_NUM"] = "1.3"
        os.environ["DC_INT_NUM"] = "2"
        os.environ["DC_BOOL_VAR"] = "true"

        assert dataconf.env("DC", Example) == Example(
            hello=None, world="monde", float_num=1.3, int_num=2, bool_var=True
        )

        os.environ.pop("DC_WORLD")
        os.environ.pop("DC_FLOAT_NUM")
        os.environ.pop("DC_INT_NUM")
        os.environ.pop("DC_BOOL_VAR")

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("t", True),
            ("y", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("f", False),
            ("n", False),
            (" false ", False),
        ],
    )
    def test_env_bool_string_cast(self, raw: str, expected: bool) -> None:
        @dataclass
        class Example:
            var: bool

        os.environ["DC_VAR"] = raw
        try:
            assert dataconf.env("DC", Example) == Example(var=expected)
        finally:
            os.environ.pop("DC_VAR")

    @pytest.mark.parametrize("raw", ["maybe", "2", "", "enabled"])
    def test_env_bool_unrecognised_raises(self, raw: str) -> None:
        @dataclass
        class Example:
            var: bool

        os.environ["DC_VAR"] = raw
        try:
            with pytest.raises(TypeConfigException):
                dataconf.env("DC", Example)
        finally:
            os.environ.pop("DC_VAR")

    def test_env_nested_bool_false(self) -> None:
        @dataclass
        class Nested:
            enabled: bool

        @dataclass
        class Example:
            nested: Nested
            flags: List[bool]

        os.environ["DC_NESTED__ENABLED"] = "false"
        os.environ["DC_FLAGS_0"] = "false"
        os.environ["DC_FLAGS_1"] = "true"
        try:
            assert dataconf.env("DC", Example) == Example(
                nested=Nested(enabled=False), flags=[False, True]
            )
        finally:
            os.environ.pop("DC_NESTED__ENABLED")
            os.environ.pop("DC_FLAGS_0")
            os.environ.pop("DC_FLAGS_1")

    def test_cli_bool_false(self) -> None:
        @dataclass
        class Example:
            var: bool

        assert dataconf.cli(["--var", "false"], Example) == Example(var=False)

    def test_env_does_not_disable_strict_globally(self) -> None:
        @dataclass
        class Example:
            n: int

        os.environ["DC_N"] = "1"
        try:
            assert dataconf.env("DC", Example) == Example(n=1)
        finally:
            os.environ.pop("DC_N")

        with pytest.raises(TypeConfigException):
            dataconf.dict({"n": "1"}, Example)

    def test_env_strict_kwarg_overrides_default(self) -> None:
        @dataclass
        class Example:
            n: int

        os.environ["DC_N"] = "1"
        try:
            with pytest.raises(TypeConfigException):
                dataconf.env("DC", Example, strict=True)
            assert dataconf.env("DC", Example) == Example(n=1)
        finally:
            os.environ.pop("DC_N")

    def test_bool_not_cast_to_int_when_non_strict(self) -> None:
        @dataclass
        class Example:
            n: int

        with pytest.raises(TypeConfigException):
            dataconf.multi.dict({"n": True}).env("DC_NONE").on(Example)

    @pytest.fixture
    def named_temporary_file(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        yield tfile
        tfile.close()

    def test_dump_fail_54(self, named_temporary_file):
        @dataclass
        class Config:
            experiment_name: str

        original = Config("test_dump")

        dataconf.dump(named_temporary_file.name, original, out="yaml")
        validate = dataconf.file(named_temporary_file.name, Config)

        assert original == validate

    @pytest.mark.skipif(not PY310up, reason="Test only runs for version 3.10+")
    def test_union_alt_syntax_112(self):
        @dataclass
        class Borked:
            foo: str | int

        assert dataconf.dict({"foo": 123}, Borked) == Borked(foo=123)
        assert dataconf.dict({"foo": "asdf"}, Borked) == Borked(foo="asdf")

        @dataclass
        class BorkedOpt:
            foo: Optional[str | int]

        assert dataconf.dict({"foo": None}, BorkedOpt) == BorkedOpt(foo=None)
        assert dataconf.dict({}, BorkedOpt) == BorkedOpt(foo=None)
        assert dataconf.dict({"foo": 123}, BorkedOpt) == BorkedOpt(foo=123)
        assert dataconf.dict({"foo": "asdf"}, BorkedOpt) == BorkedOpt(foo="asdf")
