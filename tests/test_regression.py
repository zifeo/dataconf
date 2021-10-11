from abc import ABCMeta
from dataclasses import dataclass
from typing import Optional
from typing import Text

from dataconf import loads


class TestParser:
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
