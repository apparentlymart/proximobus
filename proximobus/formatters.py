
from django.utils import simplejson as json
from xml.etree import ElementTree
import StringIO

from proximobus import service
from proximobus import model
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


KML_PREFIX = "{http://www.opengis.net/kml/2.2}"
KML_DOCUMENT = KML_PREFIX+"Document"
KML_PLACEMARK = KML_PREFIX+"Placemark"
KML_NAME = KML_PREFIX+"name"
KML_POINT = KML_PREFIX+"Point"
KML_COORDINATES = KML_PREFIX+"coordinates"

def add_kml_elem(obj, etree):
    if isinstance(obj, model._GenericList):
        for item in obj.items:
            add_kml_elem(item, etree)
        return
    elif isinstance(obj, model.Vehicle):
        name = "%s (%s)" % (obj.route_id, obj.id)
        latitude = obj.latitude
        longitude = obj.longitude
    elif isinstance(obj, model.Stop):
        name = obj.display_name
        latitude = obj.latitude
        longitude = obj.longitude
    else:
        raise service.NotFoundError("KML format is not supported for this object")

    doc_elem = etree.find(KML_DOCUMENT)
    p_elem = ElementTree.Element(KML_PLACEMARK)
    name_elem = ElementTree.Element(KML_NAME)
    name_elem.text = name
    pm_elem = ElementTree.Element(KML_POINT)
    coords_elem = ElementTree.Element(KML_COORDINATES)
    coords_elem.text = "%f,%f" % (longitude, latitude)
    pm_elem.append(coords_elem)
    p_elem.append(name_elem)
    p_elem.append(pm_elem)
    style_elem = ElementTree.fromstring("<Style xmlns='http://www.opengis.net/kml/2.2'><IconStyle><Icon><href>http://www.nextmuni.com/googleMap/images/stopMarkerRed.gif</href></Icon><scale>0.25</scale></IconStyle></Style>")
    p_elem.append(style_elem)
    doc_elem.append(p_elem)


def format_kml(obj):
    etree = ElementTree.ElementTree(ElementTree.fromstring("<kml xmlns='http://www.opengis.net/kml/2.2'><Document /></kml>"))
    add_kml_elem(obj, etree)
    output = StringIO.StringIO()
    etree.write(output)
    response = Response()
    response.content = output.getvalue()
    response.content_type = "application/vnd.google-earth.kml+xml"
    return response

formatters["kml"] = format_kml
