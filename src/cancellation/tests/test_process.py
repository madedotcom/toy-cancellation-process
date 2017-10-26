from uuid import uuid4
from expects import expect, equal, be_a
from cancellation.process import Cancellation, events


class When_creating_a_new_cancellation_process:

    correlation_id = uuid4()
    order_id = 'ORDER-123456'

    def because_we_create_a_new_process(self):
        self.process = Cancellation.start(self.correlation_id, self.order_id)

    def it_should_have_raised_cancellation_requested(self):
        [event] = self.process.new_events
        expect(event).to(be_a(Cancellation.requested))


class When_handling_cancellation_requested:

    cancellation_id = uuid4()
    order_id = 'ORDER-123456'

    def because_a_cancellation_has_been_started(self):
        self.cancellation = Cancellation([
            Cancellation.requested(self.cancellation_id, self.order_id)
        ])

    def it_should_have_the_correct_order_id(self):
        expect(self.cancellation.order_id).to(equal(self.order_id))

    def it_should_have_the_correct_cancellation(self):
        expect(self.cancellation.id).to(equal(self.cancellation_id))

