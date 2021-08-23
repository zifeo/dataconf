from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Text
from typing import Union

from dateutil.relativedelta import relativedelta


@dataclass
class Nested:
    a: Text


@dataclass
class TestConf:
    num: int
    float_amount: float
    str_name: Text
    data_list: List[Text]
    nested: Nested
    nestedList: List[Nested]
    optional: Optional[Text]
    union: Union[Text, int]
    duration: relativedelta
