"""
Script to create test transactions for settlement testing
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from transactions.models import TransactionDetail

def create_test_transactions():
    """Create test transactions for today that can be settled"""
    
    # Delete any existing test transactions for today
    today = datetime.now().date()
    TransactionDetail.objects.filter(
        trans_date__date=today,
        client_code__startswith='TEST'
    ).delete()
    
    # Create new test transactions
    test_transactions = []
    
    for i in range(5):
        txn = TransactionDetail.objects.create(
            txn_id=f"TEST_TXN_{today.strftime('%Y%m%d')}_{i+1:03d}",
            client_code=f"TEST_CLIENT_{(i % 3) + 1}",
            client_name=f"Test Client {(i % 3) + 1}",
            act_amount=Decimal(random.randint(1000, 10000)),
            status="SUCCESS",
            trans_date=datetime.now() - timedelta(hours=random.randint(1, 12)),
            is_settled=False,
            payment_mode="CARD" if i % 2 == 0 else "UPI",
            bank_name="HDFC" if i % 3 == 0 else "ICICI" if i % 3 == 1 else "SBI",
            payee_email=f"testpayee{i+1}@example.com",
            paid_amount=float(random.randint(1000, 10000))
        )
        test_transactions.append(txn)
        print(f"Created transaction: {txn.txn_id} - Amount: ₹{txn.act_amount}")
    
    print(f"\n✅ Created {len(test_transactions)} test transactions for settlement")
    print(f"These transactions are from today and eligible for T+1 settlement tomorrow")
    print("\nTo settle these transactions:")
    print("1. Go to the Settlement page in frontend")
    print("2. Click 'Create Batch' button")
    print("3. Select tomorrow's date (T+1 settlement)")
    print("4. The batch will be created with these transactions")
    print("5. Click 'Process' to process the settlement")

if __name__ == "__main__":
    create_test_transactions()