from datetime import date
from functools import wraps


class Clock:

    val = None

    @classmethod
    def fix(cls, val):
        cls.val = val

    @classmethod
    def unfix(cls):
        cls.val = None

    @classmethod
    def today(cls):
        return cls.val or date.today()

    @classmethod
    def utcnow(cls):
        return cls.val or datetime.utcnow()

type_builders = {}

def event_type(name):
    def wrapper(cls):
        cls.__name__ = name
        type_builders[name] = lambda d: cls(**d)
        return cls
    return wrapper



def handles(t):
    """
    This decorator just adds a new field to the func object
    `_handles` which describes the event type handled by
    the func
    """
    def wrapper(func):
        func._handles = t
        return func
    return wrapper


class EventRegistry(type):

    """
    Extends the `type` metaclass to add an event registry to
    classes.

    When initialising a new class, we iterate the members of
    the class looking for a _handles property and add them
    to a dict so we can do event dispatch later.
    """
    def __new__(metacls, name, bases, namespace, **kwds):
        result = type.__new__(metacls, name, bases, dict(namespace))
        result._handlers = {
                value._handles: value for value in namespace.values() if hasattr(value, '_handles')
            }
        # Extend handlers with the values from the inheritance chain
        for b in bases:
            if(b._handlers):
                for h in b._handlers:
                    result._handlers[h] = b._handlers[h]
        return result


class Aggregate(metaclass=EventRegistry):

    """
    Base class for event sourced aggregates
    """

    @classmethod
    def get_stream(cls, id):
        return cls.__name__ + '-' + str(id)

    def __init__(self, events=[]):
        self.events = events
        self.new_events = []
        self.replay()


    def replay(self):
        for e in self.events:
            self.handle(e)

    def handle(self, e):
        print (type(self).__name__ + " " + self.id + " handling event " + repr(e))
        handler = self._handlers.get(type(e))
        if handler:
            handler(self, e)
        else:
            print("no handler found")

    def write_event(self, e):
        self.handle(e)
        self.events.append(e)
        self.new_events.append(e)

