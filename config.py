import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chama-kenya-dev-secret-change-in-production')
    
    # Database
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///chama.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # M-Pesa Daraja
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'https://your-domain.com/mpesa/callback')
    MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')  # sandbox or production
    
    # Africa's Talking SMS
    AT_USERNAME = os.environ.get('AT_USERNAME', 'sandbox')
    AT_API_KEY = os.environ.get('AT_API_KEY', '')
    AT_SENDER_ID = os.environ.get('AT_SENDER_ID', 'CHAMAAPP')
    
    # Simulation flags (set to false when you have real credentials)
    SIMULATE_PAYMENTS = os.environ.get('SIMULATE_PAYMENTS', 'true').lower() == 'true'
    SIMULATE_SMS = os.environ.get('SIMULATE_SMS', 'true').lower() == 'true'
