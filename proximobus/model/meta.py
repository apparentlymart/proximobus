"""
Module containing the magic stuff that makes the models work.
"""


class Field(object):
    __slots__ = []

    # Most of the time we don't need to do anything special on out
    # because in already normalized things for us.
    def transform_out(self, value):
        return value


class PrimitiveField(Field):
    __slots__ = [ "func" ]

    def __init__(self, func):
        self.func = func

    def transform_in(self, value):
        return self.func(value)


class ObjectField(Field):
    __slots__ = [ "cls" ]

    def __init__(self, cls):
        self.cls = cls

    def transform_in(self, value):
        return value.__dict__

    def transform_out(self, value):
        ret = self.cls()
        ret.__dict__ = value
        return ret


class ListField(Field):
    __slots__ = [ "item_field" ]

    def __init__(self, item_field):
        self.item_field = item_field

    def transform_in(self, value):
        return map(lambda i : self.item_field.transform_in(i), value)

    def transform_out(self, value):
        return map(lambda i : self.item_field.transform_out(i), value)


class ModelType(type):

    def __new__(cls, name, bases, attrs):

        field_names = []

        # Replace all of the field objects in the class
        # with descriptors that'll handle their attribute
        # access.
        for k in attrs:
            field = attrs[k]
            if isinstance(field, Field):
                attrs[k] = FieldDescriptor(k, field)
                field_names.append(k)

        def as_dictionary(self):
            return self.__dict__
        attrs["as_dictionary"] = as_dictionary

        attrs["field_names"] = field_names

        ret = type.__new__(cls, name, bases, attrs)
        return ret


class Object(object):
    __metaclass__ = ModelType


class FieldDescriptor(object):
    __slots__ = ["name", "field"]

    def __init__(self, name, field):
        self.name = name
        self.field = field

    def __get__(self, instance, owner):
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            return None

        if value is None:
            return value
        else:
            return self.field.transform_out(value)

    def __set__(self, instance, value):
        if value is not None:
            value = self.field.transform_in(value)

        instance.__dict__[self.name] = value
        if value is None:
            del instance.__dict__[self.name]

