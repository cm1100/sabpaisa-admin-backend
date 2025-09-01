"""
Script to add initial payment methods data
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from clients.payment_config_models import PaymentMethod, PaymentConfiguration

def add_payment_methods():
    """Add basic payment methods"""
    
    # Create payment methods if they don't exist
    payment_methods = [
        {
            'method_name': 'Credit Card',
            'method_type': 'CARD',
            'description': 'Credit card payments via payment gateway',
            'is_active': True,
            'processing_fee_percentage': Decimal('2.00'),
            'processing_fee_fixed': Decimal('0.00'),
            'settlement_cycle': 'T+2'
        },
        {
            'method_name': 'Debit Card', 
            'method_type': 'CARD',
            'description': 'Debit card payments via payment gateway',
            'is_active': True,
            'processing_fee_percentage': Decimal('1.50'),
            'processing_fee_fixed': Decimal('0.00'),
            'settlement_cycle': 'T+1'
        },
        {
            'method_name': 'UPI',
            'method_type': 'UPI',
            'description': 'UPI payments',
            'is_active': True,
            'processing_fee_percentage': Decimal('0.50'),
            'processing_fee_fixed': Decimal('0.00'),
            'settlement_cycle': 'T+1'
        },
        {
            'method_name': 'Net Banking',
            'method_type': 'NET_BANKING',
            'description': 'Net banking payments',
            'is_active': True,
            'processing_fee_percentage': Decimal('1.00'),
            'processing_fee_fixed': Decimal('5.00'),
            'settlement_cycle': 'T+1'
        },
        {
            'method_name': 'Wallet',
            'method_type': 'WALLET',
            'description': 'Digital wallet payments',
            'is_active': True,
            'processing_fee_percentage': Decimal('1.20'),
            'processing_fee_fixed': Decimal('0.00'),
            'settlement_cycle': 'T+0'
        }
    ]
    
    created_methods = []
    for method_data in payment_methods:
        method, created = PaymentMethod.objects.get_or_create(
            method_name=method_data['method_name'],
            defaults=method_data
        )
        if created:
            created_methods.append(method)
            print(f"✓ Created payment method: {method.method_name}")
        else:
            print(f"• Payment method already exists: {method.method_name}")
    
    print(f"\n✅ Payment methods setup complete")
    print(f"Total methods in database: {PaymentMethod.objects.count()}")
    
    return created_methods

if __name__ == "__main__":
    add_payment_methods()