

from xml.etree import ElementTree
from urllib import urlencode
import logging


STATIONS_URL = "http://api.bart.gov/api/stn.aspx"
ESTIMATES_URL = "http://api.bart.gov/api/etd.aspx"
ROUTES_URL = "http://api.bart.gov/api/route.aspx"


STANDARD_CACHE_TIME = 604800
REALTIME_CACHE_TIME = 30


API_KEY = "MW9S-E7SL-26DU-VV8V"


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


def make_stations_url(command, *args):
    real_args = []
    real_args.append(('cmd', command))
    real_args.append(('key', API_KEY))
    real_args.extend(args)
    return '?'.join([STATIONS_URL, urlencode(real_args, True)])


def make_estimates_url(command, *args):
    real_args = []
    real_args.append(('cmd', command))
    real_args.append(('key', API_KEY))
    real_args.extend(args)
    return '?'.join([ESTIMATES_URL, urlencode(real_args, True)])


def make_routes_url(command, *args):
    real_args = []
    real_args.append(('cmd', command))
    real_args.append(('key', API_KEY))
    real_args.extend(args)
    return '?'.join([ROUTES_URL, urlencode(real_args, True)])


def fetch_stations_url(*args, **kwargs):
    url = make_stations_url(*args, **kwargs)
    return fetch_xml(url)


def fetch_estimates_url(*args, **kwargs):
    url = make_estimates_url(*args, **kwargs)
    return fetch_xml(url)


def fetch_routes_url(*args, **kwargs):
    url = make_routes_url(*args, **kwargs)
    return fetch_xml(url)


_pcache = {}
def memoize_in_cache(key_name, expire_time):
    def decorator(orig_func):
        def func(*args):
            full_key_name = ":".join(("bart", key_name, ",".join(args)))
            if full_key_name in _pcache:
                return _pcache[full_key_name]
            if _cache is not None:
                cacheval = _cache.get(full_key_name)
                if cacheval is not None:
                    import pickle
                    return pickle.loads(cacheval)

            ret = orig_func(*args)

            if ret is not None:
                _pcache[full_key_name] = ret
                if _cache is not None:
                    import pickle
                    cacheval = pickle.dumps(ret, 2)
                    _cache.set(full_key_name, cacheval, expire_time)

            return ret
        return func
    return decorator


@memoize_in_cache("routes", STANDARD_CACHE_TIME)
def get_all_routes():
    etree = fetch_routes_url("routes")
    ret = []
    for elem in etree.findall("routes/route"):
        ret.append(Route.from_elem(elem))
    return ret


@memoize_in_cache("routes_by_dest", STANDARD_CACHE_TIME)
def get_routes_by_destination():
    routes = get_all_routes()
    ret = {}
    for route in routes:
        destination = route.destination
        if not destination in ret:
            ret[destination] = {}
        ret[destination][route.number] = route
    return ret


@memoize_in_cache("route_by_sta_and_dest", STANDARD_CACHE_TIME)
def get_route_by_station_and_destination(station_abbr, destination):
    routes_by_destination = get_routes_by_destination()
    station = get_station_info(station_abbr)
    for routes in (station.north_routes, station.south_routes):
        for route_number in routes:
            if route_number in routes_by_destination[destination]:
                return routes_by_destination[destination][route_number]


@memoize_in_cache("route_info", STANDARD_CACHE_TIME)
def get_route_info(number):
    etree = fetch_routes_url("routeinfo", ('route', number))
    ret = []
    for elem in etree.findall("routes/route"):
        return RouteInfo.from_elem(elem)


@memoize_in_cache("station_info", STANDARD_CACHE_TIME)
def get_station_info(abbr):
    etree = fetch_stations_url("stninfo", ('orig', abbr))
    ret = []
    for elem in etree.findall("stations/station"):
        return Station.from_elem(elem)


@memoize_in_cache("estimates", REALTIME_CACHE_TIME)
def get_estimates_for_platform(station_abbr, platform):
    etree = fetch_estimates_url("etd", ("orig", station_abbr), ("plat", platform))
    ret = []
    for station_elem in etree.findall("station"):
        for eta_elem in station_elem.findall("eta"):
            for estimate_elem in eta_elem.findall("estimate"):
                ret.append(Estimate.from_elems(station_elem, eta_elem, estimate_elem))
    return ret


def _standard_repr(self):
    return "%s(%s)" % (self.__class__.__name__, self.__dict__)


class Route:
    number = None
    name = None
    origin = None
    destination = None
    __repr__ = _standard_repr

    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        ret = cls()
        ret.number = elem.findtext("number")
        ret.name = elem.findtext("name")
        abbr = elem.findtext("abbr")
        ends = abbr.split("-")
        ret.origin = ends[0]
        ret.destination = ends[1]
        return ret


class RouteInfo:
    number = None
    name = None
    color = None
    origin = None
    destination = None
    __repr__ = _standard_repr

    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        ret = cls()
        ret.number = elem.findtext("number")
        ret.name = elem.findtext("name")
        ret.color = elem.findtext("color")
        ret.origin = elem.findtext("origin")
        ret.destination = elem.findtext("destination")
        return ret


class Station:
    abbr = None
    name = None
    north_routes = None
    south_routes = None
    north_platforms = None
    south_platforms = None
    latitude = None
    longitude = None
    __repr__ = _standard_repr

    __init__ = _autoinit()

    @classmethod
    def from_elem(cls, elem):
        ret = cls()
        ret.abbr = elem.findtext("abbr")
        ret.name = elem.findtext("name")
        ret.latitude = elem.findtext("latitude")
        ret.longitude = elem.findtext("longitude")
        ret.north_platforms = []
        ret.south_platforms = []
        ret.north_routes = []
        ret.south_routes = []
        for platform_elem in elem.findall("north_platforms/platform"):
            ret.north_platforms.append(platform_elem.text.strip())
        for platform_elem in elem.findall("south_platforms/platform"):
            ret.south_platforms.append(platform_elem.text.strip())

        for route_elem in elem.findall("north_routes/route"):
            route_thing = route_elem.text.strip()
            parts = route_thing.split(" ")
            route_number = parts[1]
            ret.north_routes.append(route_number)

        for route_elem in elem.findall("south_routes/route"):
            route_thing = route_elem.text.strip()
            parts = route_thing.split(" ")
            route_number = parts[1]
            ret.south_routes.append(route_number)

        return ret

    def has_platform(self, number):
        if number in self.north_platforms or number in self.south_platforms:
            return True
        else:
            return False


class Estimate:
    destination = None
    minutes = None
    platform = None
    route = None
    __repr__ = _standard_repr

    __init__ = _autoinit()

    @classmethod
    def from_elems(cls, station_elem, eta_elem, estimate_elem):
        ret = cls()
        ret.destination = eta_elem.findtext("abbreviation")
        ret.platform = estimate_elem.findtext("platform")
        ret.minutes = estimate_elem.findtext("minutes")
        
        if ret.minutes == "Arrived":
            ret.minutes = 0

        # In order to get the route we actually have do other calls
        # to find a route that ends at the given destination.
        # There might be more than one route that matches, but it
        # doesn't really matter as long as the destination is right.
        # Hopefully we have these cached already...
        station_abbr = station_elem.findtext("abbr")
        route = get_route_by_station_and_destination(station_abbr, ret.destination)
        ret.route = route.number

        return ret
