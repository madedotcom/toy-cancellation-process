from uuid import uuid4
from expects import expect, equal, be_a, be_true
from cancellation.process.model import CancellationProcess, CancelOrderInLegacyWarehouse
from cancellation.process import messages


class When_creating_a_new_cancellation_process:

    correlation_id = str(uuid4())
    order_id = 'ORDER-123456'

    def because_we_create_a_new_process(self):
        self.process = CancellationProcess.request(self.correlation_id, self.order_id)

    def it_should_have_raised_cancellation_requested(self):
        [event, _] = self.process.new_events
        expect(event).to(be_a(CancellationProcess.requested))

    def it_should_have_raised_cancellation_requested_at_legacy_service(self):
        [_, event] = self.process.new_events
        expect(event).to(be_a(CancellationProcess.asked_warehouse_to_cancel))

    def it_should_have_raised_a_new_command(self):
        [command] = self.process.new_commands
        expect(command).to(be_a(CancelOrderInLegacyWarehouse))
        expect(command.order_id).to(equal(self.order_id))
        expect(command.correlation_id).to(equal(self.correlation_id))

    def it_should_be_waiting_for_warehouse(self):
        expect(self.process.state).to(equal('waiting_for_warehouse'))


def When_warehouse_approves_the_cancellation:

    correlation_id = str(uuid4())
    order_id = 'ORDER-123456'

    def given_a_process(self):
        self.process = CancellationProcess([
            CancellationProcess.requested(
                correlation_id,
                order_id
            )])

    def because_we_approve_the_cancellation:
        self.process.handle(
            CancellationProcess.approved(self.correlation_id))

    def it_should_be_approved(self):
        expect(self.process.state).to(equal('approved'))

    def it_should_not_create_any_new_commands(
