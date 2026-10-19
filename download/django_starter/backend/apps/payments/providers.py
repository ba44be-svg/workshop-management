"""
Payment Providers — ۳ درگاه پرداخت با Abstract Factory
زرین‌پال، آیدی‌پی، پارسیان
"""
import logging
import requests
from abc import ABC, abstractmethod
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PaymentGatewayInterface(ABC):
    """رابط اصلی درگاه‌های پرداخت"""

    @abstractmethod
    def request_authority(
        self,
        *,
        amount: Decimal,
        callback_url: str,
        description: str,
        mobile: str = None,
    ) -> Dict:
        """درخواست Authority برای شروع پرداخت"""
        pass

    @abstractmethod
    def verify(
        self,
        *,
        authority: str,
        amount: Decimal,
    ) -> Dict:
        """تأیید نهایی پرداخت"""
        pass

    @abstractmethod
    def refund(self, *, authority: str, amount: Decimal) -> Dict:
        """بازگشت وجه"""
        pass


class ZarinpalGateway(PaymentGatewayInterface):
    """درگاه پرداخت زرین‌پال"""

    BASE_URL = "https://api.zarinpal.com/v1"
    SANDBOX_URL = "https://sandbox.zarinpal.com/pg/v4"

    def __init__(self):
        self.merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
        self.callback_url = getattr(settings, 'ZARINPAL_CALLBACK_URL', '')
        self.is_sandbox = getattr(settings, 'DEBUG', False)

    @property
    def request_url(self):
        return f"{self.SANDBOX_URL if self.is_sandbox else self.BASE_URL}/request.json"

    @property
    def verify_url(self):
        return f"{self.SANDBOX_URL if self.is_sandbox else self.BASE_URL}/verify.json"

    @property
    def redirect_url(self):
        base = self.SANDBOX_URL if self.is_sandbox else "https://www.zarinpal.com/pg"
        return f"{base}/StartPay/"

    def request_authority(
        self,
        *,
        amount: Decimal,
        callback_url: str,
        description: str,
        mobile: str = None,
    ) -> Dict:
        try:
            data = {
                'merchant_id': self.merchant_id,
                'amount': int(amount),
                'callback_url': callback_url,
                'description': description,
            }
            if mobile:
                data['mobile'] = mobile

            response = requests.post(self.request_url, json=data, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('data', {}).get('code') == 100:
                authority = data['data']['authority']
                return {
                    'success': True,
                    'authority': authority,
                    'redirect_url': f"{self.redirect_url}{authority}",
                }
            return {
                'success': False,
                'error': data.get('errors', {}).get('message', 'Unknown error'),
                'code': data.get('data', {}).get('code'),
            }
        except Exception as e:
            logger.error(f'Zarinpal request failed: {e}')
            return {'success': False, 'error': str(e)}

    def verify(self, *, authority: str, amount: Decimal) -> Dict:
        try:
            data = {
                'merchant_id': self.merchant_id,
                'authority': authority,
                'amount': int(amount),
            }
            response = requests.post(self.verify_url, json=data, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('data', {}).get('code') == 100:
                return {
                    'verified': True,
                    'ref_id': str(data['data']['ref_id']),
                    'card_pan': data['data'].get('card_pan', ''),
                }
            return {
                'verified': False,
                'error': data.get('errors', {}).get('message', 'Verification failed'),
            }
        except Exception as e:
            logger.error(f'Zarinpal verify failed: {e}')
            return {'verified': False, 'error': str(e)}

    def refund(self, *, authority: str, amount: Decimal) -> Dict:
        # زرین‌پال refund API خاصی دارد
        try:
            url = f"{self.BASE_URL}/refund.json"
            data = {
                'merchant_id': self.merchant_id,
                'authority': authority,
                'amount': int(amount),
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                'refunded': data.get('data', {}).get('code') == 100,
                'error': data.get('errors', {}).get('message'),
            }
        except Exception as e:
            return {'refunded': False, 'error': str(e)}


class IDPayGateway(PaymentGatewayInterface):
    """درگاه پرداخت آیدی‌پی"""

    BASE_URL = "https://api.idpay.ir/v1.1"

    def __init__(self):
        self.api_key = getattr(settings, 'IDPAY_API_KEY', '')
        self.callback_url = getattr(settings, 'IDPAY_CALLBACK_URL', '')

    def request_authority(
        self,
        *,
        amount: Decimal,
        callback_url: str,
        description: str,
        mobile: str = None,
    ) -> Dict:
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'X-SANDBOX': '1' if getattr(settings, 'DEBUG', False) else '0',
                'Content-Type': 'application/json',
            }
            data = {
                'order_id': f'ord-{int(amount)}-{int(authority[:8]) if authority else "00000000"}',
                'amount': int(amount),
                'callback': callback_url,
                'name': '',
                'phone': mobile or '',
                'desc': description,
            }
            response = requests.post(
                f"{self.BASE_URL}/index",
                json=data,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if 'id' in data:
                return {
                    'success': True,
                    'authority': data['id'],
                    'redirect_url': f"https://idpay.ir/p/ws/{data['id']}" if
                    getattr(settings, 'DEBUG', False) else f"https://idpay.ir/p/{data['id']}",
                }
            return {'success': False, 'error': data.get('error_message', 'Unknown')}
        except Exception as e:
            logger.error(f'IDPay request failed: {e}')
            return {'success': False, 'error': str(e)}

    def verify(self, *, authority: str, amount: Decimal) -> Dict:
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'X-SANDBOX': '1' if getattr(settings, 'DEBUG', False) else '0',
                'Content-Type': 'application/json',
            }
            data = {
                'id': authority,
                'order_id': f'ord-{int(amount)}-verify',
                'amount': int(amount),
            }
            response = requests.post(
                f"{self.BASE_URL}/verify",
                json=data,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 100:
                return {
                    'verified': True,
                    'ref_id': data.get('track_id', ''),
                    'card_pan': data.get('payment', {}).get('card_no', ''),
                }
            return {'verified': False, 'error': data.get('error_message', 'Verify failed')}
        except Exception as e:
            return {'verified': False, 'error': str(e)}

    def refund(self, *, authority: str, amount: Decimal) -> Dict:
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'X-SANDBOX': '1' if getattr(settings, 'DEBUG', False) else '0',
            }
            response = requests.post(
                f"{self.BASE_URL}/{authority}/refund",
                json={'amount': int(amount)},
                headers=headers,
                timeout=10,
            )
            return {'refunded': response.status_code == 200}
        except Exception as e:
            return {'refunded': False, 'error': str(e)}


class ParsianGateway(PaymentGatewayInterface):
    """درگاه پرداخت بانک پارسیان"""

    BASE_URL = "https://pec.shaparak.ir/NewApi"

    def __init__(self):
        self.pin_code = getattr(settings, 'PARSIAN_PIN_CODE', '')
        self.callback_url = getattr(settings, 'PARSIAN_CALLBACK_URL', '')

    def request_authority(
        self,
        *,
        amount: Decimal,
        callback_url: str,
        description: str,
        mobile: str = None,
    ) -> Dict:
        try:
            data = {
                'pin': self.pin_code,
                'amount': int(amount),
                'callback': callback_url,
                'description': description,
                'mobile': mobile or '',
            }
            response = requests.post(
                f"{self.BASE_URL}/api/RequestToken",
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get('Status') == 0 and data.get('Token'):
                return {
                    'success': True,
                    'authority': data['Token'],
                    'redirect_url': f"https://pec.shaparak.ir/NewApi/RunPurchase?Token={data['Token']}",
                }
            return {'success': False, 'error': data.get('Message', 'Unknown')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify(self, *, authority: str, amount: Decimal) -> Dict:
        try:
            data = {
                'pin': self.pin_code,
                'token': authority,
                'status': 0,
            }
            response = requests.post(
                f"{self.BASE_URL}/api/ConfirmPayment",
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get('Status') == 0:
                return {
                    'verified': True,
                    'ref_id': str(data.get('RRN', '')),
                    'card_pan': data.get('CardNumber', ''),
                }
            return {'verified': False, 'error': data.get('Message', 'Verify failed')}
        except Exception as e:
            return {'verified': False, 'error': str(e)}

    def refund(self, *, authority: str, amount: Decimal) -> Dict:
        try:
            data = {
                'pin': self.pin_code,
                'token': authority,
                'amount': int(amount),
            }
            response = requests.post(
                f"{self.BASE_URL}/api/Reversal",
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            return {'refunded': response.json().get('Status') == 0}
        except Exception as e:
            return {'refunded': False, 'error': str(e)}


class GatewayFactory:
    """کارخانه درگاه‌های پرداخت — انتخاب درگاه"""

    GATEWAYS = {
        'zarinpal': ZarinpalGateway,
        'idpay': IDPayGateway,
        'parsian': ParsianGateway,
    }

    DEFAULT_GATEWAY = 'zarinpal'

    @classmethod
    def create_gateway(cls, gateway_name: str = None) -> PaymentGatewayInterface:
        """ساخت یک instance از درگاه مشخص‌شده"""
        gateway_name = gateway_name or cls.DEFAULT_GATEWAY
        gateway_class = cls.GATEWAYS.get(gateway_name)
        if not gateway_class:
            raise ValueError(f'Unknown gateway: {gateway_name}')
        return gateway_class()

    @classmethod
    def get_available_gateways(cls) -> list:
        """لیست درگاه‌های موجود"""
        return list(cls.GATEWAYS.keys())
