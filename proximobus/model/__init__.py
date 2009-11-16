"""
Classes defining the external data model of ProximoBus.
"""


from proximobus.model.meta import Object, PrimitiveField, ObjectField, ListField


def List(item_field):
    class List(Object):
        items = ListField(item_field)

        def __init__(self, items):
            self.items = items

    return List


class Agency(Object):
    id = PrimitiveField(str)
    display_name = PrimitiveField(str)

    @classmethod
    def from_nextbus(cls, nb_agency):
        ret = cls()
        ret.id = nb_agency.tag
        ret.display_name = nb_agency.title
        return ret


class RouteRef(Object):
    id = PrimitiveField(str)
    display_name = PrimitiveField(str)
    
    @classmethod
    def from_nextbus(cls, nb_route):
        ret = cls()
        ret.id = nb_route.tag
        ret.display_name = nb_route.title
        return ret

class Route(Object):
    id = PrimitiveField(str)
    display_name = PrimitiveField(str)
    fg_color = PrimitiveField(str)
    bg_color = PrimitiveField(str)

    @classmethod
    def from_nextbus(cls, nb_route):
        ret = cls()
        ret.id = nb_route.route.tag
        ret.display_name = nb_route.route.title
        ret.bg_color = "#"+nb_route.color
        ret.fg_color = "#"+nb_route.opposite_color
        return ret


class Run(Object):
    id = PrimitiveField(str)
    display_name = PrimitiveField(str)
    route_id = PrimitiveField(str)

    @classmethod
    def from_nextbus(cls, nb_dir):
        ret = cls()
        ret.id = nb_dir.tag
        ret.display_name = nb_dir.title
        ret.route_id = nb_dir.route.tag
        return ret


class RunOnRoute(Run):
    display_in_ui = PrimitiveField(bool)

    @classmethod
    def from_nextbus(cls, nb_dir):
        supe = Run.from_nextbus(nb_dir)
        ret = cls()
        ret.__dict__ = supe.__dict__
        ret.display_in_ui = nb_dir.use_for_ui
        return ret
    

class Stop(Object):
    id = PrimitiveField(str)
    title = PrimitiveField(str)
    latitude = PrimitiveField(float)
    longitude = PrimitiveField(float)

    @classmethod
    def from_nextbus(cls, nb_stop):
        ret = cls()
        ret.id = nb_stop.tag
        ret.display_name = nb_stop.title
        ret.latitude = nb_stop.latitude
        ret.longitude = nb_stop.longitude
        return ret


class StopOnRoute(Stop):
    primary_run_id = PrimitiveField(str)

    @classmethod
    def from_nextbus(cls, nb_stop):
        supe = Stop.from_nextbus(nb_stop)
        ret = cls()
        ret.__dict__ = supe.__dict__
        ret.primary_run_id = nb_stop.direction_tag
        return ret
    

class Vehicle(Object):
    id = PrimitiveField(str)
    latitude = PrimitiveField(float)
    longitude = PrimitiveField(float)
    route_id = PrimitiveField(str)
    run_id = PrimitiveField(str)
    seconds_since_report = PrimitiveField(int)
    predictable = PrimitiveField(bool)
    heading = PrimitiveField(float)
    leading_vehicle_id = PrimitiveField(str)


class Prediction(Object):
    run_id = PrimitiveField(str)
    minutes = PrimitiveField(float)
    is_departing = PrimitiveField(bool)
    block_id = PrimitiveField(str)
