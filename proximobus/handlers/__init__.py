
from proximobus import formatters
from proximobus import service
from proximobus import model
from proximobus.model.meta import Object, PrimitiveField, ObjectField
from proximobus.handlers import nextbus_handlers
from proximobus.handlers import bart_handlers

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

            if agency_id == "bart":
                agency_handlers = bart_handlers
            else:
                # Default is NextBus
                agency_handlers = nextbus_handlers
            
            if num_chunks == 2:
                ret = agency_handlers.handle_agency(agency_id)
            elif path_chunks[2] == "routes":
                if num_chunks == 3:
                    ret = agency_handlers.handle_route_list(agency_id)
                else:
                    route_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = agency_handlers.handle_route(agency_id, route_id)
                    elif path_chunks[4] == "stops":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_route_stops(agency_id, route_id)
                        else:
                            stop_id = path_chunks[5]
                            if num_chunks == 6:
                                ret = agency_handlers.handle_route_stop(agency_id, route_id, stop_id)
                    elif path_chunks[4] == "runs":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_route_runs(agency_id, route_id)
                        else:
                            run_id = path_chunks[5]
                            if num_chunks == 6:
                                ret = agency_handlers.handle_route_run(agency_id, route_id, run_id)
                            elif path_chunks[6] == "stops":
                                if num_chunks == 7:
                                    ret = agency_handlers.handle_route_run_stops(agency_id, route_id, run_id)
                    elif path_chunks[4] == "vehicles":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_route_vehicles(agency_id, route_id)
            elif path_chunks[2] == "vehicles":
                if num_chunks == 3:
                    ret = agency_handlers.handle_agency_vehicles(agency_id)
                else:
                    vehicle_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = agency_handlers.handle_single_vehicle(agency_id, vehicle_id)
            elif path_chunks[2] == "stops":
                if num_chunks == 3:
                    # There is no endpoint to retrieve a list of all stops across a whole agency
                    raise service.NotFoundError()
                else:
                    stop_id = path_chunks[3]
                    if num_chunks == 4:
                        ret = agency_handlers.handle_single_stop(agency_id, stop_id)
                    elif path_chunks[4] == "messages":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_stop_messages(agency_id, stop_id)
                    elif path_chunks[4] == "routes":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_stop_routes(agency_id, stop_id)
                    elif path_chunks[4] == "predictions":
                        if num_chunks == 5:
                            ret = agency_handlers.handle_stop_predictions(agency_id, stop_id)
                        elif path_chunks[5] == "by-route":
                            if num_chunks == 7:
                                route_id = path_chunks[6]
                                ret = agency_handlers.handle_stop_predictions(agency_id, stop_id, route_id)

    if ret is None:
        raise service.NotFoundError()

    return formatter(ret)


def handle_agency_list():
    agencies = nextbus_handlers.get_agencies()
    agencies.append(model.Agency.bart())
    return model.List(ObjectField(model.Agency))(agencies)


