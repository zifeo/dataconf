import argparse
import sys
import importlib.util
from dataconf import load

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c", "--conf", dest="conf", action="store", help="config file", required=True
)
parser.add_argument(
    "-m", "--module", dest="module", action="store", help="module", required=True
)
parser.add_argument(
    "-d",
    "--dataclass",
    dest="dataclass",
    action="store",
    help="dataclass path",
    required=True,
)


def run():
    args = parser.parse_args()

    module = importlib.import_module(args.module)
    clazz = getattr(module, args.dataclass)

    res = load(args.conf, clazz)
    print(res)
    sys.exit(0)
    
