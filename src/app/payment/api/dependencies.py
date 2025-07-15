from src.app.payment.model.payment import PaymentTransaction
from src.app.payment.repository.payment import PaymentTransactionRepository
from src.app.payment.service.payment import PaymentService

payment_repository = PaymentTransactionRepository(PaymentTransaction)
payment_service = PaymentService(payment_repository)
