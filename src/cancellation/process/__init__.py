from cancellation.process.model import event_type, handles, Aggregate
from typing import NamedTuple, NewType
from uuid import UUID


OrderId = NewType('LocationCode', str)
CancellationId = NewType('CancellationId', UUID)

class Cancellation(model.Aggregate):

    @event_type('cancellation_requested')
    class requested (NamedTuple):
        cancellation_id: CancellationId
        order_id: OrderId


    def __init__(self, events=[]):
        self.id = "not-started"
        model.Aggregate.__init__(self, events)

    @classmethod
    def start(cls, cancellation_id, order_id):
        cancellation = cls()
        evt = Cancellation.requested(cancellation_id, order_id)
        cancellation.write_event(evt)
        return cancellation

    @handles(requested)
    def on_started(self, e):
        self.id = e.cancellation_id
        self.order_id = e.order_id
