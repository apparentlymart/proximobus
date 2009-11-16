
from os import environ

class Request:
    format = None
    path_chunks = None

    @classmethod
    def from_cgi_environment(cls):
        self = cls()
        if environ["REQUEST_METHOD"] != "GET":
            raise MethodNotAllowedError()
        
        uri = environ["PATH_INFO"]
        parts = uri.split(".")
        if len(parts) != 2:
            raise NotFoundError("No format extension provided")
        self.format = parts[1]
        self.path_chunks = parts[0].split("/")
        # Since the path starts with a slash we end up with a redundant empty string on the front
        self.path_chunks.remove('')
        return self

    def __repr__(self):
        return "<Request for "+("/".join(self.path_chunks))+">"


class Response:
    content_type = None
    content = None


class HTTPError(Exception):
    status = 500


class NotFoundError(HTTPError):
    status = 404


class MethodNotAllowedError(HTTPError):
    status = 405
