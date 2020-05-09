import argparse
import sys
import importlib.util
from dataconf import load, dumps
from pyhocon import HOCONConverter
from dataconf.utils import FileType

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
parser.add_argument(
    "-o",
    "--out",
    dest="out",
    action="store",
    help=f"out file type: {', '.join(e.value for e in FileType)}",
    required=False,
)


def run():
    args = parser.parse_args()

    module = importlib.import_module(args.module)
    clazz = getattr(module, args.dataclass)

    out = None
    if args.out:
        out = FileType[args.out.upper()]

    res = load(args.conf, clazz)
    print(dumps(res, out))

    sys.exit(0)
