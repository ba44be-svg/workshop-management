"""
Core exceptions
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class InsufficientStockError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'موجودی کافی نیست'
    default_code = 'insufficient_stock'


class NearExpiryWarning(APIException):
    status_code = status.HTTP_200_OK  # Not an error, just a warning
    default_detail = 'کالای نزدیک به انقضا'
    default_code = 'near_expiry'


class JournalNotBalancedError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'سند حسابداری نامتوازن است'
    default_code = 'journal_not_balanced'


class CreditLimitExceededError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'سقف اعتبار فروشگاه کافی نیست'
    default_code = 'credit_limit_exceeded'


class PaymentGatewayError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'خطای درگاه پرداخت'
    default_code = 'payment_gateway_error'


class SamanTaxError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'خطای سامانه سامان'
    default_code = 'saman_tax_error'


class ApprovalRequiredError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'این عمل نیازمند تأیید مدیر است'
    default_code = 'approval_required'
