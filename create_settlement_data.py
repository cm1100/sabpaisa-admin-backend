"""
Script to create transactions eligible for immediate settlement
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from transactions.models import TransactionDetail

def create_settlement_eligible_transactions():
    """Create transactions from yesterday that can be settled today"""
    
    # Get yesterday's date for T+1 settlement
    yesterday = datetime.now() - timedelta(days=1)
    
    # Delete any existing test transactions from yesterday
    TransactionDetail.objects.filter(
        trans_date__date=yesterday.date(),
        client_code__startswith='TEST'
    ).delete()
    
    # Create new test transactions from yesterday
    test_transactions = []
    
    print(f"Creating transactions from {yesterday.date()} for T+1 settlement today...")
    
    for i in range(10):  # Create 10 transactions
        # Create timezone-aware datetime for yesterday
        trans_time = timezone.make_aware(
            datetime.combine(
                yesterday.date(),
                datetime.min.time().replace(
                    hour=random.randint(8, 20),
                    minute=random.randint(0, 59)
                )
            )
        )
        
        txn = TransactionDetail.objects.create(
            txn_id=f"SETTLE_TXN_{yesterday.strftime('%Y%m%d')}_{i+1:03d}",
            client_code=f"TEST_CLIENT_{(i % 3) + 1}",
            client_name=f"Test Client {(i % 3) + 1}",
            act_amount=Decimal(random.randint(5000, 50000)),
            status="SUCCESS",
            trans_date=trans_time,
            is_settled=False,
            payment_mode="CARD" if i % 2 == 0 else "UPI",
            bank_name="HDFC" if i % 3 == 0 else "ICICI" if i % 3 == 1 else "SBI",
            payee_email=f"customer{i+1}@example.com",
            paid_amount=float(random.randint(5000, 50000))
        )
        test_transactions.append(txn)
        print(f"Created transaction: {txn.txn_id} - Amount: ₹{txn.act_amount:,.2f} - Date: {trans_time}")
    
    total_amount = sum(txn.act_amount for txn in test_transactions)
    
    print(f"\n✅ Created {len(test_transactions)} transactions from yesterday")
    print(f"Total Amount: ₹{total_amount:,.2f}")
    print(f"\nThese transactions are eligible for T+1 settlement TODAY!")
    print("\nTo settle these transactions:")
    print("1. Go to http://localhost:3001/settlements")
    print("2. Click 'Create Batch' button")
    print(f"3. Select today's date ({datetime.now().date()})")
    print("4. The batch will be created successfully")
    print("5. Click 'Process' to process the settlement")
    
    return test_transactions

if __name__ == "__main__":
    transactions = create_settlement_eligible_transactions()