"""
M-Pesa Daraja API Integration for Chama App Kenya
Supports STK Push (Lipa Na M-Pesa Online) for contributions and loan repayments.
"""

import base64
import requests
from datetime import datetime
from flask import current_app
import json


class MpesaService:
    """Safaricom Daraja API client"""
    
    def __init__(self):
        self.consumer_key = current_app.config.get('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET', '')
        self.shortcode = current_app.config.get('MPESA_SHORTCODE', '174379')
        self.passkey = current_app.config.get('MPESA_PASSKEY', '')
        self.callback_url = current_app.config.get('MPESA_CALLBACK_URL', '')
        self.env = current_app.config.get('MPESA_ENV', 'sandbox')
        self.simulate = current_app.config.get('SIMULATE_PAYMENTS', True)
        
        if self.env == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def _get_access_token(self):
        """Generate OAuth access token"""
        if self.simulate or not self.consumer_key:
            return 'simulated_access_token'
        
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        auth = base64.b64encode(f'{self.consumer_key}:{self.consumer_secret}'.encode()).decode()
        
        headers = {'Authorization': f'Basic {auth}'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get('access_token')
    
    def _generate_password(self):
        """Generate the password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data = f'{self.shortcode}{self.passkey}{timestamp}'
        password = base64.b64encode(data.encode()).decode()
        return password, timestamp
    
    def stk_push(self, phone: str, amount: float, account_reference: str, 
                 transaction_desc: str = 'Chama Contribution') -> dict:
        """
        Initiate STK Push to customer's phone.
        
        Args:
            phone: Customer phone (2547XXXXXXXX or 07XXXXXXXX)
            amount: Amount in KES
            account_reference: Your internal reference (e.g. CONTRIB-123)
            transaction_desc: Description shown on phone
        
        Returns:
            dict with success status and CheckoutRequestID or error
        """
        # Normalize phone to 254 format
        phone = self._normalize_phone(phone)
        amount = int(amount)  # M-Pesa requires integer
        
        if self.simulate or not self.consumer_key or not self.passkey:
            # Simulation mode – perfect for demos and development
            print(f'[MPESA SIMULATE] STK Push → {phone} | KES {amount} | Ref: {account_reference}')
            return {
                'success': True,
                'simulated': True,
                'CheckoutRequestID': f'ws_CO_{datetime.now().strftime("%Y%m%d%H%M%S")}_{phone[-4:]}',
                'MerchantRequestID': f'merch_{datetime.now().strftime("%H%M%S")}',
                'ResponseDescription': 'Success. Request accepted for processing (SIMULATED)',
                'CustomerMessage': f'STK Push sent to {phone} (SIMULATED - no real charge)'
            }
        
        try:
            token = self._get_access_token()
            password, timestamp = self._generate_password()
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': amount,
                'PartyA': phone,
                'PartyB': self.shortcode,
                'PhoneNumber': phone,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference[:12],  # Max 12 chars
                'TransactionDesc': transaction_desc[:13]
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'simulated': False,
                    'CheckoutRequestID': data.get('CheckoutRequestID'),
                    'MerchantRequestID': data.get('MerchantRequestID'),
                    'ResponseDescription': data.get('ResponseDescription'),
                    'CustomerMessage': data.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('errorMessage') or data.get('ResponseDescription') or str(data)
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query the status of an STK Push transaction"""
        if self.simulate or not self.consumer_key:
            return {
                'success': True,
                'simulated': True,
                'ResultCode': '0',
                'ResultDesc': 'The service request is processed successfully. (SIMULATED)'
            }
        
        try:
            token = self._get_access_token()
            password, timestamp = self._generate_password()
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            return response.json()
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Convert 07XXXXXXXX or +2547XXXXXXXX to 2547XXXXXXXX"""
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('+'):
            phone = phone[1:]
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        if not phone.startswith('254'):
            phone = '254' + phone
        return phone
    
    @staticmethod
    def parse_callback(callback_data: dict) -> dict:
        """
        Parse the STK callback from Safaricom.
        Returns a clean dict with success, amount, phone, mpesa_receipt, etc.
        """
        try:
            body = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = body.get('ResultCode')
            result_desc = body.get('ResultDesc', '')
            checkout_id = body.get('CheckoutRequestID')
            merchant_id = body.get('MerchantRequestID')
            
            result = {
                'success': result_code == 0,
                'result_code': result_code,
                'result_desc': result_desc,
                'checkout_request_id': checkout_id,
                'merchant_request_id': merchant_id,
                'amount': None,
                'mpesa_receipt': None,
                'phone': None,
                'transaction_date': None
            }
            
            if result_code == 0:
                metadata = body.get('CallbackMetadata', {}).get('Item', [])
                for item in metadata:
                    name = item.get('Name')
                    value = item.get('Value')
                    if name == 'Amount':
                        result['amount'] = value
                    elif name == 'MpesaReceiptNumber':
                        result['mpesa_receipt'] = value
                    elif name == 'PhoneNumber':
                        result['phone'] = str(value)
                    elif name == 'TransactionDate':
                        result['transaction_date'] = str(value)
            
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
