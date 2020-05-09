from dataclasses import dataclass
from datetime import timedelta
from typing import List
from typing import Optional
from typing import Union


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
    duration: timedelta
