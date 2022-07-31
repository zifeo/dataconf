import mimetypes

from werkzeug.wrappers import Request
from werkzeug.wrappers import Response


def file_handler(path: str):
    with open("confs/simple.json", "r") as f:
        data = f.read()

    def handler(request: Request):
        return Response(data, mimetype=mimetypes.guess_type(path)[0])

    return handler
