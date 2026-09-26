"""
SMS Notifications via Africa's Talking for Chama App Kenya
Most popular SMS gateway in Kenya – works with all networks (Safaricom, Airtel, Telkom).
"""

import requests
from flask import current_app
from datetime import datetime


class SMSService:
    """Africa's Talking SMS client"""
    
    def __init__(self):
        self.username = current_app.config.get('AT_USERNAME', 'sandbox')
        self.api_key = current_app.config.get('AT_API_KEY', '')
        self.sender_id = current_app.config.get('AT_SENDER_ID', 'CHAMAAPP')
        self.simulate = current_app.config.get('SIMULATE_SMS', True)
        
        if self.username == 'sandbox':
            self.base_url = 'https://api.sandbox.africastalking.com/version1/messaging'
        else:
            self.base_url = 'https://api.africastalking.com/version1/messaging'
    
    def send(self, phone: str, message: str) -> dict:
        """
        Send an SMS to a single recipient.
        
        Args:
            phone: Phone number (07XXXXXXXX or 2547XXXXXXXX)
            message: SMS text (max ~160 chars recommended)
        
        Returns:
            dict with success status
        """
        phone = self._normalize_phone(phone)
        
        if self.simulate or not self.api_key:
            print(f'[SMS SIMULATE] To: {phone}')
            print(f'               Msg: {message}')
            return {
                'success': True,
                'simulated': True,
                'message': 'SMS simulated successfully',
                'recipients': [{'number': phone, 'status': 'Success', 'statusCode': 101}]
            }
        
        try:
            headers = {
                'ApiKey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.username,
                'to': phone,
                'message': message,
            }
            
            # Only add from if not sandbox (sandbox uses default)
            if self.username != 'sandbox' and self.sender_id:
                data['from'] = self.sender_id
            
            response = requests.post(self.base_url, data=data, headers=headers, timeout=30)
            result = response.json()
            
            # Africa's Talking returns SMSMessageData
            sms_data = result.get('SMSMessageData', {})
            recipients = sms_data.get('Recipients', [])
            
            if recipients and recipients[0].get('statusCode') in [100, 101, 102]:
                return {
                    'success': True,
                    'simulated': False,
                    'message': sms_data.get('Message', 'Sent'),
                    'recipients': recipients
                }
            else:
                return {
                    'success': False,
                    'error': sms_data.get('Message') or str(result),
                    'recipients': recipients
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_bulk(self, phones: list, message: str) -> dict:
        """Send same message to multiple recipients"""
        results = []
        success_count = 0
        for phone in phones:
            res = self.send(phone, message)
            results.append({'phone': phone, **res})
            if res.get('success'):
                success_count += 1
        return {
            'success': success_count > 0,
            'total': len(phones),
            'sent': success_count,
            'results': results
        }
    
    # ========== Pre-built Chama notification templates ==========
    
    def notify_contribution_received(self, phone: str, member_name: str, 
                                      amount: float, chama_name: str, 
                                      new_balance: float) -> dict:
        msg = (
            f"Habari {member_name.split()[0]}, "
            f"your contribution of KES {amount:,.0f} to {chama_name} has been received. "
            f"New balance: KES {new_balance:,.0f}. "
            f"- ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_loan_approved(self, phone: str, member_name: str, 
                              amount: float, chama_name: str, 
                              total_repayable: float) -> dict:
        msg = (
            f"Habari {member_name.split()[0]}, "
            f"your loan of KES {amount:,.0f} from {chama_name} has been APPROVED. "
            f"Total repayable: KES {total_repayable:,.0f}. "
            f"- ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_loan_rejected(self, phone: str, member_name: str, 
                              amount: float, chama_name: str) -> dict:
        msg = (
            f"Habari {member_name.split()[0]}, "
            f"your loan application of KES {amount:,.0f} from {chama_name} was not approved. "
            f"Contact your treasurer for details. - ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_loan_repayment(self, phone: str, member_name: str, 
                               amount: float, remaining: float, 
                               chama_name: str) -> dict:
        msg = (
            f"Habari {member_name.split()[0]}, "
            f"loan repayment of KES {amount:,.0f} received for {chama_name}. "
            f"Remaining balance: KES {remaining:,.0f}. - ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_mgr_payout(self, phone: str, member_name: str, 
                           amount: float, round_number: int, 
                           chama_name: str) -> dict:
        msg = (
            f"Hongera {member_name.split()[0]}! "
            f"It is your turn for Merry-Go-Round Round #{round_number} in {chama_name}. "
            f"You will receive KES {amount:,.0f}. - ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_meeting(self, phone: str, member_name: str, 
                        title: str, meeting_date: str, 
                        location: str, chama_name: str) -> dict:
        msg = (
            f"Habari {member_name.split()[0]}, "
            f"Meeting reminder for {chama_name}: {title} "
            f"on {meeting_date}"
            f"{' at ' + location if location else ''}. "
            f"- ChamaApp"
        )
        return self.send(phone, msg)
    
    def notify_stk_sent(self, phone: str, amount: float, purpose: str) -> dict:
        msg = (
            f"Please complete the M-Pesa prompt on your phone for KES {amount:,.0f} "
            f"({purpose}). Enter your PIN to confirm. - ChamaApp"
        )
        return self.send(phone, msg)
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('+'):
            phone = phone[1:]
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        if not phone.startswith('254'):
            phone = '254' + phone
        return '+' + phone  # Africa's Talking prefers +254 format
