"""
Script to add more transactions eligible for settlement
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

def add_more_transactions():
    """Create more transactions from yesterday for settlement today"""
    
    # Get yesterday's date for T+1 settlement
    yesterday = datetime.now() - timedelta(days=1)
    
    # Create 20 new transactions from yesterday
    test_transactions = []
    
    print(f"Adding 20 more transactions from {yesterday.date()} for T+1 settlement today...")
    
    for i in range(20):
        # Create timezone-aware datetime for yesterday
        trans_time = timezone.make_aware(
            datetime.combine(
                yesterday.date(),
                datetime.min.time().replace(
                    hour=random.randint(6, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
            )
        )
        
        # Generate unique transaction ID
        txn_id = f"TXN_{yesterday.strftime('%Y%m%d')}_{random.randint(1000, 9999)}_{i+1:03d}"
        
        # Random client selection
        clients = [
            ("RETAIL001", "ABC Retail Store"),
            ("ECOM002", "XYZ E-Commerce"),
            ("FOOD003", "Food Delivery Co"),
            ("TECH004", "Tech Solutions Ltd"),
            ("PHARMA005", "MediCare Pharmacy"),
        ]
        client_code, client_name = random.choice(clients)
        
        # Random payment modes and banks
        payment_modes = ["CARD", "UPI", "NET_BANKING", "WALLET"]
        banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "PNB", "BOB"]
        
        amount = Decimal(random.randint(1000, 100000))
        
        txn = TransactionDetail.objects.create(
            txn_id=txn_id,
            client_code=client_code,
            client_name=client_name,
            act_amount=amount,
            paid_amount=float(amount),
            payee_amount=amount,
            status="SUCCESS",
            trans_date=trans_time,
            is_settled=False,
            payment_mode=random.choice(payment_modes),
            bank_name=random.choice(banks),
            payee_email=f"customer_{random.randint(100, 999)}@email.com",
            pg_txn_id=f"PG{random.randint(100000, 999999)}",
            bank_txn_id=f"BANK{random.randint(100000, 999999)}",
        )
        test_transactions.append(txn)
        print(f"✓ {txn.txn_id} | {client_name} | ₹{amount:,.2f} | {txn.payment_mode}")
    
    total_amount = sum(txn.act_amount for txn in test_transactions)
    
    print(f"\n" + "="*60)
    print(f"✅ Successfully added {len(test_transactions)} transactions")
    print(f"📊 Total Amount: ₹{total_amount:,.2f}")
    print(f"📅 Transaction Date: {yesterday.date()}")
    print(f"📆 Eligible for Settlement: {datetime.now().date()} (Today)")
    print("="*60)
    print("\n🎯 Next Steps:")
    print("1. Go to http://localhost:3001/settlements")
    print("2. Click 'Create Batch' button")
    print(f"3. Select today's date: {datetime.now().date()}")
    print("4. Batch will be created with all eligible transactions")
    print("5. Click 'Process' to complete the settlement")
    
    return test_transactions

if __name__ == "__main__":
    transactions = add_more_transactions()