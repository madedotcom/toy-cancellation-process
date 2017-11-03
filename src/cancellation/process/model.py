from transitions import Machine
from datetime import date
from functools import wraps
from uuid import UUID, uuid4
from typing import NamedTuple, NewType

OrderId = NewType('LocationCode', str)
CancellationId = NewType('CancellationId', UUID)

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
        self.events.append(e)
        self.new_events.append(e)
        self.handle(e)



class ProcessManager(Aggregate):

    def __init__(self, events=[]):
        super().__init__(events)
        self.new_commands = []

    def checkpoint(self):
        self.new_events = []
        self.new_commands = []


class CancelOrderInLegacyWarehouse(NamedTuple):

    order_id: str
    message_id: UUID
    correlation_id: CancellationId


class CancellationProcess (ProcessManager):

    states = ['not_stated', 'started', 'waiting_for_warehouse', 'rejected', 'approved', 'waiting_for_hacienda', 'waiting_for_erp']

    transitions = [
            { 'trigger': 'start', 'source': 'not_started', 'dest': 'started' },
            { 'trigger': 'tell_warehouse', 'source': 'started', 'dest': 'waiting_for_warehouse' },
            { 'trigger': 'approve', 'source': 'waiting_for_warehouse', 'dest': 'approved' },
            { 'trigger': 'reject', 'source': 'waiting_for_warehouse', 'dest': 'rejected' },
            { 'trigger': 'do_next', 'source': 'waiting_for_warehouse', 'dest': 'waiting_for_hacienda' },
    ]


    @event_type('cancellation_requested')
    class requested (NamedTuple):
        cancellation_id: CancellationId
        order_id: OrderId

    @event_type('legacy_cancellation_requested')
    class asked_warehouse_to_cancel (NamedTuple):
        cancellation_id: CancellationId
        order_id: OrderId

    def __init__(self, events=[]):
        self.id = "not-stated"
        super().__init__(events)
        self.machine = Machine(
                model=self,
                states=CancellationProcess.states,
                transitions=CancellationProcess.transitions,
                initial='not_started')

    @handles(requested)
    def on_requested(self, e):
        self.id = str(e.cancellation_id)
        self.order_id = e.order_id
        self.start()
        self.ask_warehouse_to_cancel()

    @classmethod
    def request(cls, cancellation_id, order_id):
        cancellation = cls()
        evt = CancellationProcess.requested(cancellation_id, order_id)
        cancellation.write_event(evt)
        return cancellation

    def ask_warehouse_to_cancel(self):
        evt = CancellationProcess.asked_warehouse_to_cancel(
            self.id,
            self.order_id
        )
        self.write_event(evt)

    @handles(asked_warehouse_to_cancel)
    def when_asking_warehouse_to_cancel(self, e):
        self.new_commands.append(CancelOrderInLegacyWarehouse(self.order_id, uuid4(), self.id))
        self.tell_warehouse()
