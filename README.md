# Dataconf

[![Actions Status](https://github.com/zifeo/dataconf/workflows/CI/badge.svg)](https://github.com/zifeo/dataconf/actions)
[![PyPI version](https://badge.fury.io/py/dataconf.svg)](https://badge.fury.io/py/dataconf)

Lightweight configuration with automatic dataclasses parsing (hocon/json/yaml/properties files).

## Getting started

Requires at least Python 3.8.

```bash
# pypi
pip install dataconf
poetry add dataconf

# master
pip install --upgrade git+https://github.com/zifeo/dataconf.git
poetry add git+https://github.com/zifeo/dataconf.git

# dev
poetry install
pre-commit install
```

## Usage

```python
from dataclasses import dataclass, field
from typing import List, Dict, Text, Union
from dateutil.relativedelta import relativedelta
import dataconf

conf = """
str_name = test
str_name = ${HOSTNAME}
float_num = 2.2
list_data = [
    a
    b
]
nested {
    a = test
}
nested_list = [
    {
        a = test1
    }
]
duration = 2s
union = 1
"""

@dataclass
class Nested:
    a: Text

@dataclass
class Config:
    str_name: Text
    float_num: float
    list_data: List[Text]
    nested: Nested
    nested_list: List[Nested]
    duration: relativedelta
    union: Union[Text, int]
    default: Text = 'hello'
    default_factory: Dict[Text, Text] = field(default_factory=dict)

print(dataconf.load(conf, Config))
# TestConf(test='pc.home', float=2.1, default='hello', list=['a', 'b'], nested=Nested(a='test'), nested_list=[Nested(a='test1')], duration=relativedelta(seconds=+2), default_factory={}, union=1)

# Replicating pureconfig Scala sealed trait case class behavior
# https://pureconfig.github.io/docs/overriding-behavior-for-sealed-families.html
class InputType:
    """
    Abstract base class
    """
    pass
    
    
@dataclass(init=True, repr=True)
class StringImpl(InputType):
    name: Text
    age: Text

    def test_method(self):
        print(f"{self.name} is {self.age} years old.")

        
@dataclass(init=True, repr=True)
class IntImpl(InputType):
    area_code: int
    phone_num: Text

    def test_method(self):
        print(f"The area code for {self.phone_num} is {str(self.area_code)}")

        
@dataclass
class Base:
    location: Text
    input_source: InputType

str_conf = """
{
    location: Europe
    input_source {
        name: Thailand
        age: "12"
    }
}
"""

conf = dataconf.loads(str_conf, Base)
```

```python
import dataconf

conf = dataconf.loads('confs/test.hocon', Config)
conf = dataconf.loads('confs/test.json', Config)
conf = dataconf.loads('confs/test.yaml', Config)
conf = dataconf.loads('confs/test.properties', Config)

dataconf.dumps('confs/test.hocon', out='hocon')
dataconf.dumps('confs/test.json', out='json')
dataconf.dumps('confs/test.yaml', out='yaml')
dataconf.dumps('confs/test.properties', out='properties')
```

Follows same api as python JSON package (e.g. `load`, `loads`, `dump`, `dumps`). 
For full HOCON capabilities see [here](https://github.com/chimpler/pyhocon/#example-of-hocon-file).

## CI

```shell
dataconf -c confs/test.hocon -m tests.configs -d TestConf -o hocon
# dataconf.exceptions.TypeConfigException: expected type <class 'datetime.timedelta'> at .duration, got <class 'int'>
```
