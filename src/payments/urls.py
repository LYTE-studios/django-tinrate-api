from django.urls import path, include
from views.payments_release_views import ReleasePaymentView
from views.payments_cancel_views import ChargeCancellationFeeView
from views.payments_capture_views import CapturePaymentView
from views.payments_intent_views import CreatePaymentIntentView
from views.payments_refund_views import RefundPaymentView
from views.payments_fail_views import FailPaymentsView

urlpatterns = [
    path('intent/', CreatePaymentIntentView.as_view(), name='capture_payment'),
    path('capture/', CapturePaymentView.as_view(), name='capture_payment'),
    path('release/', ReleasePaymentView.as_view(), name='release_payment'),
    path('refund/', RefundPaymentView.as_view(), name='refund_payment'),
    path('cancel/', ChargeCancellationFeeView.as_view(), name='capture_payment'),
    path('fail/', FailPaymentsView.as_view(), name='fail_payment'),
]
