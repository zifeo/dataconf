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

# remote master
pip install --upgrade git+https://github.com/zifeo/dataconf.git
poetry add git+https://github.com/zifeo/dataconf.git

# local repo/dev
poetry install
pre-commit install
```

## Usage

```python
import os
from dataclasses import dataclass, field
from typing import List, Dict, Text, Union
from dateutil.relativedelta import relativedelta
import dataconf

conf = """
str_name = test
str_name = ${?HOME}
dash-to-underscore = true
float_num = 2.2
# this is a comment
list_data = [
    a
    b
]
nested {
    a = test
    b : 1
}
nested_list = [
    {
        a = test1
        b : 2.5
    }
]
duration = 2s
union = 1
people {
    name = Thailand
}
zone {
    area_code = 42
}
"""

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
    default: Text = 'hello'
    default_factory: Dict[Text, Text] = field(default_factory=dict)

print(dataconf.string(conf, Config))
# Config(
#   str_name='/users/root',
#   dash_to_underscore=True,
#   float_num=2.2,
#   list_data=['a', 'b'],
#   nested=Nested(a='test'),
#   nested_list=[Nested(a='test1', b=2.5)],
#   duration=relativedelta(seconds=+2), 
#   union=1, 
#   people=Person(name='Thailand'), 
#   zone=Zone(area_code=42),
#   default='hello', 
#   default_factory={}
# )

@dataclass
class Example:
    hello: string
    world: string

os.environ['DC_WORLD'] = 'monde'

print(
    dataconf.multi
    .url('https://raw.githubusercontent.com/zifeo/dataconf/master/confs/simple.hocon')
    .env('DC')
    .on(Example)
)
# Example(hello='bonjour',world='monde')
```

## API

```python
import dataconf

conf = dataconf.string('{ name: Test }', Config)
conf = dataconf.env('PREFIX_', Config)
conf = dataconf.url('https://raw.githubusercontent.com/zifeo/dataconf/master/confs/test.hocon', Config)
conf = dataconf.file('confs/test.{hocon,json,yaml,properties}', Config)

# Same api as Python json/yaml packages (e.g. `load`, `loads`, `dump`, `dumps`)
conf = dataconf.load('confs/test.{hocon,json,yaml,properties}', Config)
dataconf.dump('confs/test.hocon', conf, out='hocon')
dataconf.dump('confs/test.json', conf, out='json')
dataconf.dump('confs/test.yaml', conf, out='yaml')
dataconf.dump('confs/test.properties', conf, out='properties')
```

For full HOCON capabilities see [here](https://github.com/chimpler/pyhocon/#example-of-hocon-file).

## Env dict/list parsing

```bash
PREFIX_VAR=a
PREFIX_VAR_NAME=b
PREFIX_TEST__NAME=c
PREFIX_LS_0=d
PREFIX_LS_1=e
PREFIX_LSLS_0_0=f
PREFIX_LSOB_0__NAME=g
PREFIX_NESTED_="{ name: Test }"
PREFIX_SUB_="{ value: ${PREFIX_VAR} }"
```

is equivalent to

```
{
    var = a
    var_name = b
    test {
        name = c
    }
    ls = [
        d
        e
    ]
    lsls = [
        [
            f
        ]
    ]
    lsob = [
        {
            name = g
        }
    ]
    nested {
        # parse nested config by suffixing env var with `_`
        name: Test
    }
    sub {
        # will have value "a" at parsing, useful for aliases
        value = ${PREFIX_VAR}
    }
}
```

## CLI usage

Can be used for validation or converting between supported file formats (`-o`).

```shell
dataconf -c confs/test.hocon -m tests.configs -d TestConf -o hocon
# dataconf.exceptions.TypeConfigException: expected type <class 'datetime.timedelta'> at .duration, got <class 'int'>
```
