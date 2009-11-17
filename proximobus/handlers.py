
from proximobus import formatters
from proximobus import service
from proximobus import model
from proximobus.model.meta import Object, PrimitiveField, ObjectField
import nextbus
from google.appengine.api import memcache

nextbus._cache = memcache

def handle_request(request):

    formatter = formatters.formatter_for_request(request)
    if formatter is None:
        raise service.NotFoundError()

    path_chunks = request.path_chunks
    ret = None

    if len(path_chunks) == 0:
        raise service.NotFoundError()

    if len(request.query_args) > 0:
        raise service.BadRequestError("Unsupported query args")

    num_chunks = len(path_chunks)

    if path_chunks[0] == "agencies":
        if num_chunks == 1:
            ret = handle_agency_list()
        else:
            agency_id = path_chunks[1]
            if num_chunks == 2:
                ret = handle_agency(agency_id)
            elif path_chunks[2] == "routes":
                if num_chunks == 3:
                    ret = handle_route_list(agency_id)
                else:
                    route_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = handle_route(agency_id, route_id)
                    elif path_chunks[4] == "stops":
                        if num_chunks == 5:
                            ret = handle_route_stops(agency_id, route_id)
                        else:
                            stop_id = path_chunks[5]
                            if num_chunks == 6:
                                ret = handle_route_stop(agency_id, route_id, stop_id)
                    elif path_chunks[4] == "runs":
                        if num_chunks == 5:
                            ret = handle_route_runs(agency_id, route_id)
                        else:
                            run_id = path_chunks[5]
                            if num_chunks == 6:
                                ret = handle_route_run(agency_id, route_id, run_id)
                            elif path_chunks[6] == "stops":
                                if num_chunks == 7:
                                    ret = handle_route_run_stops(agency_id, route_id, run_id)
                    elif path_chunks[4] == "vehicles":
                        if num_chunks == 5:
                            ret = handle_route_vehicles(agency_id, route_id)
            elif path_chunks[2] == "vehicles":
                if num_chunks == 3:
                    ret = handle_agency_vehicles(agency_id)
                else:
                    vehicle_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = handle_single_vehicle(agency_id, vehicle_id)
            elif path_chunks[2] == "stops":
                if num_chunks == 3:
                    # There is no endpoint to retrieve a list of all stops across a whole agency
                    raise service.NotFoundError()
                else:
                    stop_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = handle_single_stop(agency_id, stop_id)
                    elif path_chunks[4] == "messages":
                        if num_chunks == 5:
                            ret = handle_stop_messages(agency_id, stop_id)
                    elif path_chunks[4] == "routes":
                        if num_chunks == 5:
                            ret = handle_stop_routes(agency_id, stop_id)
                    elif path_chunks[4] == "predictions":
                        if num_chunks == 5:
                            ret = handle_stop_predictions(agency_id, stop_id)
                        elif path_chunks[5] == "by-route":
                            if num_chunks == 7:
                                route_id = path_chunks[6]
                                ret = handle_stop_predictions(agency_id, stop_id, route_id)

    if ret is None:
        raise service.NotFoundError()

    return formatter(ret)


def handle_agency_list():
    nextbus_agencies = nextbus.get_all_agencies()
    agencies = map(lambda nb_a : model.Agency.from_nextbus(nb_a), nextbus_agencies)
    return model.List(ObjectField(model.Agency))(agencies)

def handle_agency(agency_id):
    nextbus_agencies = nextbus.get_all_agencies()
    for nb_a in nextbus_agencies:
        if nb_a.tag == agency_id:
            return model.Agency.from_nextbus(nb_a)
    raise service.NotFoundError()

def handle_route_list(agency_id):
    nextbus_routes = nextbus.get_all_routes_for_agency(agency_id)
    routes = map(lambda nb_r : model.RouteRef.from_nextbus(nb_r), nextbus_routes)
    return model.List(ObjectField(model.RouteRef))(routes)

def handle_route(agency_id, route_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    return model.Route.from_nextbus(route_config)

def handle_route_stops(agency_id, route_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    stops = map(lambda nb_s : model.StopOnRoute.from_nextbus(nb_s), route_config.stops)
    return model.List(ObjectField(model.Stop))(stops)
    
def handle_route_stop(agency_id, route_id, stop_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    for nb_s in route_config.stops:
        if nb_s.tag == stop_id:
            return model.StopOnRoute.from_nextbus(nb_s)
    raise service.NotFoundError()
    
def handle_route_runs(agency_id, route_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    runs = map(lambda nb_d : model.RunOnRoute.from_nextbus(nb_d), route_config.directions)
    return model.List(ObjectField(model.RunOnRoute))(runs)
    
def handle_route_run(agency_id, route_id, run_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    for nb_d in route_config.directions:
        if nb_d.tag == run_id:
            return model.RunOnRoute.from_nextbus(nb_d)
    raise service.NotFoundError()
    
def handle_route_run_stops(agency_id, route_id, run_id):
    route_config = nextbus.get_route_config(agency_id, route_id)
    stops = map(lambda nb_s : model.StopOnRoute.from_nextbus(nb_s), route_config.directions_dict[run_id].stops)
    return model.List(ObjectField(model.Stop))(stops)
    
def handle_route_vehicles(agency_id, route_id):
    nb_vehicles = nextbus.get_vehicle_locations_on_route(agency_id, route_id)
    vehicles = map(lambda nb_v : model.Vehicle.from_nextbus(nb_v), nb_vehicles)
    return model.List(ObjectField(model.Vehicle))(vehicles)

def handle_agency_vehicles(agency_id):
    nb_vehicles = nextbus.get_all_vehicle_locations(agency_id)
    vehicles = map(lambda nb_v : model.Vehicle.from_nextbus(nb_v), nb_vehicles)
    return model.List(ObjectField(model.Vehicle))(vehicles)

def handle_single_vehicle(agency_id, vehicle_id):
    nb_vehicles = nextbus.get_all_vehicle_locations(agency_id)
    for nb_v in nb_vehicles:
        if nb_v.id == vehicle_id:
            return model.Vehicle.from_nextbus(nb_v)
    return None

def handle_single_stop(agency_id, stop_id):
    nb_preds = nextbus.get_predictions_for_stop(agency_id, stop_id)
    ret = model.StopRef()
    ret.display_name = nb_preds.stop_title
    ret.id = stop_id
    if ret.display_name is not None:
        return ret
    else:
        return None


def handle_stop_messages(agency_id, stop_id):
    nb_preds = nextbus.get_predictions_for_stop(agency_id, stop_id)

    if nb_preds.stop_title is None:
        return None

    return model.List(PrimitiveField(str))(nb_preds.messages)


def handle_stop_routes(agency_id, stop_id):
    nb_preds = nextbus.get_predictions_for_stop(agency_id, stop_id)

    if nb_preds.stop_title is None:
        return None

    nb_routes = {}
    for nb_d in nb_preds.directions:
        nb_routes[nb_d.route.tag] = nb_d.route

    routes = map(lambda nb_r : model.RouteRef.from_nextbus(nb_r), nb_routes.values())

    return model.List(ObjectField(model.RouteRef))(routes)


def handle_stop_predictions(agency_id, stop_id, route_id = None):
    nb_preds = nextbus.get_predictions_for_stop(agency_id, stop_id)

    if nb_preds.stop_title is None:
        return None

    if route_id is not None:
        nb_preds = filter(lambda nb_p : nb_p.direction.route.tag == route_id, nb_preds.predictions)
    else:
        nb_preds = nb_preds.predictions

    predictions = map(lambda nb_p : model.Prediction.from_nextbus(nb_p), nb_preds)

    return model.List(ObjectField(model.Prediction))(predictions)


