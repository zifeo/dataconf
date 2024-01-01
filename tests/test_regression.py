from abc import ABCMeta
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
import os
import tempfile
from typing import Dict
from typing import List
from typing import Optional
from typing import Text
from typing import Union
import pytest

import dataconf
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
