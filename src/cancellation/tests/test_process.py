from uuid import uuid4
from expects import expect, equal, be_a, be_true
from cancellation.process import Cancellation, messages


class When_creating_a_new_cancellation_process:

    correlation_id = uuid4()
    order_id = 'ORDER-123456'

    def because_we_create_a_new_process(self):
        self.process = Cancellation.start(self.correlation_id, self.order_id)

    def it_should_have_raised_cancellation_requested(self):
        [event] = self.process.new_events
        expect(event).to(be_a(Cancellation.requested))


class SpyMinion:

    def __init__(self):
        self.was_told = False

    def tell(self, cmd):
        self.was_told = True


class When_handling_cancellation_requested:

    cancellation_id = uuid4()
    order_id = 'ORDER-123456'

    def given_a_warehouse(self):
        self.warehouse = SpyMinion()

    def because_a_cancellation_has_been_started(self):
        events = [Cancellation.requested(self.cancellation_id, self.order_id)]
        self.cancellation = Cancellation(events, warehouse=self.warehouse)

    def it_should_have_the_correct_order_id(self):
        expect(self.cancellation.order_id).to(equal(self.order_id))

    def it_should_have_the_correct_cancellation(self):
        expect(self.cancellation.id).to(equal(self.cancellation_id))

    def it_should_have_told_the_warehouse_to_attempt_cancellation(self):
        expect(self.warehouse.was_told).to(be_true)

