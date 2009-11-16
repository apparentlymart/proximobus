
from django.utils import simplejson as json

from proximobus.service import Response


formatters = {}


def format_json(obj):
    # FIXME: Should turn the key names into camel case, since that's more JSONy
    dict = obj.as_dictionary()
    response = Response()
    response.content = json.dumps(dict)
    response.content_type = "application/json"
    return response

formatters["json"] = format_json


def format_js(obj):
    ret = format_json(obj)
    callback_func = "callback"
    ret.content_type = "text/javascript"
    ret.content = "%s(%s)" % (callback_func, ret.content)
    return ret

formatters["js"] = format_js
