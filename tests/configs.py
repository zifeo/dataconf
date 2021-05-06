from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Union

from dateutil.relativedelta import relativedelta


@dataclass
class Nested:
    a: str


@dataclass
class TestConf:
    int: int
    float: float
    str: str
    list: List[str]
    nested: Nested
    nestedList: List[Nested]
    optional: Optional[str]
    union: Union[str, int]
    duration: relativedelta
