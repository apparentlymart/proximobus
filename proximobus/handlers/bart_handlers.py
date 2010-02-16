
from proximobus import model
from proximobus import service
from proximobus.model.meta import Object, PrimitiveField, ObjectField
from google.appengine.api import memcache
import bart

bart._cache = memcache

# Decorator for methods that take agency_id to avoid
# duplicating this check that agency_id == "bart"
def bart_agency(func):
    def newfunc(agency_id, *args, **kwargs):
        if agency_id == "bart":
            return func(*args, **kwargs)
        else:
            raise service.NotFoundError()
    return newfunc


# Handles the wacky way we turn stop ids into (station, platform) pairs
def bart_stop(func):
    def newfunc(stop_id, *args, **kwargs):
        parts = stop_id.split("-", 2)
        station_abbr = parts[0]
        platform = parts[1]
        return func(station_abbr, platform, *args, **kwargs)
    return newfunc


@bart_agency
def handle_agency():
    return model.Agency.bart()


@bart_agency
def handle_route_list():
    bart_routes = bart.get_all_routes()
    routes = map(lambda b_r : model.RouteRef.from_bart(b_r), bart_routes)
    return model.List(ObjectField(model.RouteRef))(routes)


@bart_agency
def handle_route(route_id):
    bart_route = bart.get_route_info(route_id)
    return model.Route.from_bart(bart_route)


@bart_agency
def handle_route_runs(route_id):
    bart_route = bart.get_route_info(route_id)
    runs = [ model.Run.from_bart(bart_route) ]
    return model.List(ObjectField(model.Run))(runs)


@bart_agency
@bart_stop
def handle_single_stop(station_abbr, platform):
    bart_station = bart.get_station_info(station_abbr)
    if bart_station.has_platform(platform):
        return model.Stop.from_bart(bart_station, platform)
    else:
        return None


@bart_agency
@bart_stop
def handle_stop_predictions(station_abbr, platform, route_id = None):
    bart_estimates = bart.get_estimates_for_platform(station_abbr, platform)
    predictions = map(lambda b_e : model.Prediction.from_bart(b_e), bart_estimates)
    predictions.sort(lambda a,b : int(a.minutes - b.minutes))
    return model.List(ObjectField(model.Prediction))(predictions)
    
