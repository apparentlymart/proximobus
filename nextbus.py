

from xml.etree import ElementTree
from urllib import urlencode


NEXTBUS_SERVICE_URL = "http://webservices.nextbus.com/service/publicXMLFeed"


def _autoinit(realinit = None):
    def auto_init(self, **kwargs):
        for k in kwargs:
            self.__dict__[k] = kwargs[k]
        if realinit is not None:
            realinit(self)
    return auto_init


_url_fetcher = None
def _init_fetcher():
    global _url_fetcher
    have_urllib2 = True
    
    try:
        import urllib2
    except:
        have_urllib2 = False

    if have_urllib2:
        def urllib2_fetcher(url):
            return urllib2.urlopen(url)
        _url_fetcher = urllib2_fetcher
_init_fetcher()


_cache = None


def set_url_fetcher(func):
    _url_fetcher = func


def fetch_xml(url):
    return ElementTree.parse(_url_fetcher(url))


def make_fetcher_method(url_func, target_class):
    def meth(self):
        if _url_fetcher is None:
            raise RuntimeError("No configured url fetcher")
        url = url_func(self)
        etree = fetch_xml(url)
        return target_class.from_etree(etree)


def make_nextbus_url(command, a = None, *args):
    real_args = []
    real_args.append(('command', command))
    if a is not None:
        real_args.append(('a', a))
    real_args.extend(args)
    return '?'.join([NEXTBUS_SERVICE_URL, urlencode(real_args, True)])


def fetch_nextbus_url(*args, **kwargs):
    url = make_nextbus_url(*args, **kwargs)
    return fetch_xml(url)


def memoize_in_cache(key_name, expire_time):
    def decorator(orig_func):
        def func(*args):
            if _cache is not None:
                full_key_name = ":".join((key_name, ",".join(args)))
                import pickle
                cacheval = _cache.get(full_key_name)
                if cacheval is not None:
                    return pickle.loads(cacheval)

            ret = orig_func(*args)

            if _cache is not None:
                if ret is not None:
                    cacheval = pickle.dumps(ret, 2)
                    _cache.set(full_key_name, cacheval)

            return ret
        return func
    return decorator


@memoize_in_cache("agencies", 604800)
def get_all_agencies():
    """
    Get a list of all agencies supported by the NextBus public API.

    Note that this does not include all agencies supported by NextBus.
    Public data is not available for some agencies despite the fact
    that they use NextBus. Hassle your local transit agency to
    enable the public data feed.
    """
    etree = fetch_nextbus_url("agencyList")
    ret = []
    for elem in etree.findall("agency"):
        ret.append(Agency.from_elem(elem))
    return ret


@memoize_in_cache("agency_routes", 604800)
def get_all_routes_for_agency(tag):
    """
    Get a list of all routes for a given agency.
    """
    etree = fetch_nextbus_url("routeList", tag)
    ret = []
    for elem in etree.findall("route"):
        ret.append(Route.from_elem(elem))
    return ret


@memoize_in_cache("route_config", 604800)
def get_route_config(agency_tag, route_tag):
    """
    Get the route configuration for a given route with in a given agency.
    """
    etree = fetch_nextbus_url("routeConfig", agency_tag, ('r', route_tag))
    elem = etree.find("route")
    return RouteConfig.from_elem(elem)


@memoize_in_cache("stop_predictions", 30)
def get_predictions_for_stop(agency_tag, stop_id):
    """
    Get the current predictions for a particular stop across all routes.
    """
    etree = fetch_nextbus_url("predictions", agency_tag, ('stopId', stop_id))
    predictions = Predictions()
    for predictions_elem in etree.findall("predictions"):
        route = Route(tag=predictions_elem.get("routeTag"), title=predictions_elem.get("routeTitle"))
        predictions.stop_title = predictions_elem.get("stopTitle")

        no_predictions_direction_title = predictions_elem.get("dirTitleBecauseNoPredictions")
        if no_predictions_direction_title:
            # record the direction but no predictions
            direction = TaglessDirection(title=no_predictions_direction_title, route=route)
            predictions.directions.append(direction)
            continue

        for message_elem in predictions_elem.findall("message"):
            predictions.messages.add(message_elem.get("text"))

        for direction_elem in predictions_elem.findall("direction"):
            direction = Direction()
            direction.route = route
            direction.title = direction_elem.get("title")
            predictions.directions.append(direction)

            for prediction_elem in direction_elem.findall("prediction"):
                prediction = Prediction()
                prediction.direction = direction
                prediction.seconds = int(prediction_elem.get("seconds"))
                prediction.minutes = int(prediction_elem.get("minutes"))
                prediction.epoch_time = int(prediction_elem.get("epochTime"))
                prediction.block = prediction_elem.get("block")

                if prediction_elem.get("isDeparture") == "true":
                    prediction.is_departing = True
                else:
                    prediction.is_departing = False

                # For some reason NextBus returns the direction tag on
                # each individual prediction rather than on the direction element.
                direction.tag = prediction_elem.get("dirTag")
                predictions.predictions.append(prediction)

            predictions.predictions.sort(lambda a,b : int(a.epoch_time - b.epoch_time))

    return predictions


@memoize_in_cache("all_vehicles", 30)
def get_all_vehicle_locations(agency_tag):
    etree = fetch_nextbus_url("vehicleLocations", agency_tag, ('t', 0))
    return map(lambda elem : Vehicle.from_elem(elem), etree.findall("vehicle"))


@memoize_in_cache("route_vehicles", 30)
def get_vehicle_locations_on_route(agency_tag, route_tag):
    etree = fetch_nextbus_url("vehicleLocations", agency_tag, ('r', route_tag), ('t', 0))
    return map(lambda elem : Vehicle.from_elem(elem), etree.findall("vehicle"))


def _standard_repr(self):
    return "%s(%s)" % (self.__class__.__name__, self.__dict__)


class Agency:
    tag = None
    title = None
    region_title = None
    __repr__ = _standard_repr

    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        ret = cls()
        ret.tag = elem.get("tag")
        ret.title = elem.get("title")
        ret.region_title = elem.get("regionTitle")
        return ret


class Route:
    tag = None
    title = None
    __repr__ = _standard_repr

    __init__ = _autoinit()


    @classmethod
    def from_elem(cls, elem):
        ret = cls()
        ret.tag = elem.get("tag")
        ret.title = elem.get("title")
        return ret


class RouteConfig:
    route = None
    color = None
    opposite_color = None
    stops_dict = None
    directions_dict = None
    __repr__ = _standard_repr

    @_autoinit
    def __init__(self):
        if self.stops_dict is None:
            self.stops_dict = {}
        if self.directions_dict is None:
            self.directions_dict = {}

    @classmethod
    def from_elem(cls, elem):
        self = cls()
        self.route = Route.from_elem(elem)
        self.color = elem.get("color")
        self.opposite_color = elem.get("oppositeColor")

        # We want to return the dict keyed on stop_id,
        # but in order to build the directions we
        # temporarily need to key on tag too.
        stops_by_tag = {}

        for stop_elem in elem.findall("stop"):
            stop = StopOnRoute.from_elem(stop_elem)
            stops_by_tag[stop.tag] = stop
            self.stops_dict[stop.stop_id] = stop

        for direction_elem in elem.findall("direction"):
            direction = DirectionOnRoute()
            direction.tag = direction_elem.get("tag")
            direction.title = direction_elem.get("title")
            direction.name = direction_elem.get("name")

            if direction_elem.get("useForUI") == "true":
                direction.use_for_ui = True
            else:
                direction.use_for_ui = False

            self.directions_dict[direction.tag] = direction

            for stop_elem in direction_elem.findall("stop"):
                tag = stop_elem.get("tag")
                try:
                    stop = stops_by_tag[tag]
                    direction.stops.append(stop)
                except KeyError:
                    # For some reason sometimes NextBus
                    # references stops that it hasn't
                    # told us about. Not much we can do.
                    pass
            
        return self

    @property
    def stops(self):
        return self.stops_dict.values()

    @property
    def directions(self):
        return self.directions_dict.values()

    def has_stop_id(stop_id):
        return stop_id in self.stops_dict


class Stop:
    tag = None
    title = None
    latitude = None
    longitude = None
    stop_id = None
    __repr__ = _standard_repr
    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        self = cls()
        self.tag = elem.get("tag")
        self.title = elem.get("title")
        self.latitude = float(elem.get("lat"))
        self.longitude = float(elem.get("lon"))
        self.stop_id = elem.get("stopId")
        return self


class StopOnRoute(Stop):
    direction_tag = None

    @classmethod
    def from_elem(cls, elem):
        stop = Stop.from_elem(elem)
        self = StopOnRoute(**stop.__dict__)
        self.direction_tag = elem.get("dirTag")
        return self

class TaglessDirection:
    """
    A direction that only has a display title and lacks a tag.
    
    In the prediction output when a particular direction has no predictions
    NextBus returns only the name of the direction and not its tag,
    so this really stupid class is used to represent that situation.
    """
    title = None
    route = None
    __repr__ = _standard_repr
    __init__ = _autoinit()


class Direction(TaglessDirection):
    tag = None


class DirectionOnRoute(Direction):
    use_for_ui = None
    stops = None
    name = None

    @_autoinit
    def __init__(self):
        if self.stops is None:
            self.stops = []

class Predictions:
    directions = None
    messages = None
    predictions = None
    stop_title = None
    __repr__ = _standard_repr

    @_autoinit
    def __init__(self):
        if self.messages is None:
            self.messages = set()
        if self.directions is None:
            self.directions = []
        if self.predictions is None:
            self.predictions = []


class Prediction:
    direction = None
    minutes = None
    seconds = None
    epoch_time = None
    is_departing = None
    block = None
    __repr__ = _standard_repr
    __init__ = _autoinit()


class Vehicle:
    id = None
    route_tag = None
    direction_tag = None
    latitude = None
    longitude = None
    seconds_since_report = None
    predictable = None
    heading = None
    leading_vehicle_id = None
    __repr__ = _standard_repr
    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        self = cls()
        self.id = elem.get("id")
        self.route_tag = elem.get("routeTag")
        self.direction_tag = elem.get("dirTag")
        self.latitude = float(elem.get("lat"))
        self.longitude = float(elem.get("lon"))
        self.seconds_since_report = int(elem.get("secsSinceReport"))
        self.heading = float(elem.get("heading"))
        self.leading_vehicle_id = elem.get("leadingVehicleId")
        self.predictable = (elem.get("predictable") == "true")

        if self.route_tag == "null":
            self.route_tag = None
        if self.direction_tag == "null":
            self.direction_tag = None
        
        return self

