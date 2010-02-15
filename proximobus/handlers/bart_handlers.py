
from proximobus import model
from proximobus import service
from proximobus.model.meta import Object, PrimitiveField, ObjectField
import bart


# Decorator for methods that take agency_id to avoid
# duplicating this check that agency_id == "bart"
def bart_agency(func):
    def newfunc(agency_id, *args, **kwargs):
        if agency_id == "bart":
            return func(*args, **kwargs)
        else:
            raise service.NotFoundError()
    return newfunc


@bart_agency
def handle_agency():
    return model.Agency.bart()


@bart_agency
def handle_route_list():
    bart_routes = bart.get_all_routes()
    routes = map(lambda b_r : model.RouteRef.from_bart(b_r), bart_routes)
    return model.List(ObjectField(model.RouteRef))(routes)


