
from proximobus.formatters import formatters
from proximobus import service
from proximobus import model
from proximobus.model.meta import Object, PrimitiveField, ObjectField
import nextbus

def handle_request(request):

    try:
        formatter = formatters[request.format]
    except KeyError:
        raise service.NotFoundError()

    path_chunks = request.path_chunks
    ret = None

    if len(path_chunks) == 0:
        raise service.NotFoundError()

    if path_chunks[0] == "agencies":
        if len(path_chunks) == 1:
            ret = handle_agency_list()
        else:
            agency_id = path_chunks[1]
            if len(path_chunks) == 2:
                ret = handle_agency(agency_id)
            elif path_chunks[2] == "routes":
                if len(path_chunks) == 3:
                    ret = handle_route_list(agency_id)
                else:
                    route_id = path_chunks[3]
                    if len(path_chunks) == 4:
                        ret = handle_route(agency_id, route_id)
                    elif path_chunks[4] == "stops":
                        if len(path_chunks) == 5:
                            ret = handle_route_stops(agency_id, route_id)
                        else:
                            stop_id = path_chunks[5]
                            if len(path_chunks) == 6:
                                ret = handle_route_stop(agency_id, route_id, stop_id)
                    

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
    
