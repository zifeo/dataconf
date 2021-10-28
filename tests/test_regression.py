from abc import ABCMeta
from dataclasses import dataclass
from dataclasses import field
import os
from os import environ
from typing import Dict
from typing import List
from typing import Optional
from typing import Text
from typing import Union

from dataconf import load
from dataconf import loads
from dateutil.relativedelta import relativedelta

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
        assert load(
            os.path.join(PARENT_DIR, "confs", "readme.hocon"), Config
        ) == Config(
            str_name=environ.get("HOME", "test"),
            dash_to_underscore=True,
            float_num=2.2,
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

        assert loads(conf, C) == C(
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

        assert loads(conf, C) == C(
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
        assert loads(conf, A) == A(a_a=False)
