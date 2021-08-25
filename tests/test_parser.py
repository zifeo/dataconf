from dataclasses import dataclass
from dataclasses import field
import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Text
from typing import Union

from dataconf import load
from dataconf import loads
from dataconf.exceptions import MissingTypeException
from dataconf.exceptions import UnexpectedKeysException
from dateutil.relativedelta import relativedelta
import pytest

from .scala_sealed_trait import InputType


PARENT_DIR = os.path.normpath(
    os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir
)


class TestParser:
    def test_simple(self) -> None:
        @dataclass
        class A:
            a: Text

        conf = """
        a = test
        """
        assert loads(conf, A) == A(a="test")

    def test_relativedelta(self) -> None:
        @dataclass
        class A:
            a: relativedelta

        conf = """
        a = 2d
        """
        assert loads(conf, A) == A(a=relativedelta(days=2))

    def test_list(self) -> None:
        @dataclass
        class A:
            a: List[Text]

        conf = """
        a = [
            test
        ]
        """
        assert loads(conf, A) == A(a=["test"])

    def test_boolean(self) -> None:
        @dataclass
        class A:
            a: bool

        conf = """
        a = false
        """
        assert loads(conf, A) == A(a=False)

    def test_dict(self) -> None:
        @dataclass
        class A:
            a: Dict[Text, Text]

        conf = """
        a {
            b = test
        }
        """
        assert loads(conf, A) == A(a={"b": "test"})

    def test_nested(self) -> None:
        @dataclass
        class B:
            a: Text

        @dataclass
        class A:
            b: B

        conf = """
        b {
            a = test
        }
        """
        assert loads(conf, A) == A(b=B(a="test"))

    def test_union(self) -> None:
        @dataclass
        class B:
            a: Text

        @dataclass
        class A:
            b: Union[B, Text]

        conf = """
        b {
            a = test
        }
        """
        assert loads(conf, A) == A(b=B(a="test"))

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_optional(self) -> None:
        @dataclass
        class A:
            b: Optional[Text] = None

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_optional_with_default(self) -> None:
        @dataclass
        class A:
            b: Optional[Text]

        conf = ""
        assert loads(conf, A) == A(b=None)

        conf = """
        b = test
        """
        assert loads(conf, A) == A(b="test")

    def test_empty_list(self) -> None:
        @dataclass
        class A:
            b: List[Text] = field(default_factory=list)

        conf = ""
        assert loads(conf, A) == A(b=[])

    def test_json(self) -> None:
        @dataclass
        class A:
            b: Text

        conf = """
        {
            "b": "c"
        }
        """
        assert loads(conf, A) == A(b="c")

    def test_yaml(self) -> None:
        @dataclass
        class A:
            b: Text

        conf = """
        b: c
        """
        assert loads(conf, A) == A(b="c")

    def test_default_value(self) -> None:
        @dataclass
        class A:
            b: Text = "c"

        assert loads("", A) == A(b="c")

    def test_root_dict(self) -> None:

        conf = """
        b: c
        """
        assert loads(conf, Dict[Text, Text]) == dict(b="c")

    def test_missing_type(self) -> None:

        with pytest.raises(MissingTypeException):
            loads("", Dict)

        with pytest.raises(MissingTypeException):
            loads("", List)

    def test_misformat(self) -> None:

        conf = """
        b {}
        c {
            f {
        }
        d {}
        }
        """

        @dataclass
        class Clazz:
            f: Dict[Text, Text] = field(default_factory=dict)

        with pytest.raises(UnexpectedKeysException):
            loads(conf, Dict[Text, Clazz])

    def test_complex_hocon(self) -> None:
        @dataclass
        class Conn:
            host: Text
            port: int
            ssl: Optional[Dict[Text, Text]] = field(default_factory=dict)

        @dataclass
        class Base:
            data_root: Text
            pipeline_name: Text
            data_type: Text
            production: bool
            conn: Optional[Conn] = None
            data_split: Optional[Dict[Text, int]] = None
            tfx_root: Optional[Text] = None
            metadata_root: Optional[Text] = None
            beam_args: Optional[List[Text]] = field(
                default_factory=lambda: [
                    "--direct_running_mode=multi_processing",
                    "--direct_num_workers=0",
                ]
            )

        conf = load(os.path.join(PARENT_DIR, "confs", "complex.hocon"), Base)

        assert conf == Base(
            data_root="/some/path/here",
            pipeline_name="Penguin-Config",
            data_type="tfrecord",
            production=True,
            conn=Conn(host="test.server.io", port=443),
        )

    def test_traits_string_impl(self) -> None:
        @dataclass
        class Base:
            location: Text
            input_source: InputType()

        str_conf = """
        {
            location: Europe
            input_source {
                name: Thailand
                age: "12"
            }
        }
        """

        conf = loads(str_conf, Base)
        assert conf == Base(
            location="Europe",
            input_source=InputType.StringImpl(name="Thailand", age="12"),
        )
        assert conf.input_source.test_method() == "Thailand is 12 years old."
        assert conf.input_source.test_complex() == 36

    def test_traits_int_impl(self) -> None:
        @dataclass
        class Base:
            location: Text
            input_source: InputType()

        str_conf = """
        {
            location: Europe
            input_source {
                area_code: 94
                phone_num: "1234567"
            }
        }
        """

        conf = loads(str_conf, Base)
        assert conf == Base(
            location="Europe",
            input_source=InputType.IntImpl(area_code=94, phone_num="1234567"),
        )
        assert conf.input_source.test_method() == "The area code for 1234567 is 94"
        assert conf.input_source.test_complex() == 84
