#!/usr/bin/env python
"""
Test Transaction API Integration
Tests search, filtering, pagination, and all transaction operations
"""

import requests
import json
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test credentials (from bootup.md)
TEST_USERNAME = "admin@sabpaisa.com"
TEST_PASSWORD = "admin123"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{API_URL}/auth/login/",
        json={"email": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", data.get("token"))
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def test_transaction_list(token):
    """Test transaction list with pagination"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test basic list
    print("\n1. Testing basic transaction list...")
    response = requests.get(
        f"{API_URL}/transactions/transactions/",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data.get('count', 0)} transactions")
        print(f"   Page: {data.get('current_page', 1)}/{data.get('total_pages', 1)}")
        if data.get('results'):
            print(f"   First transaction: {data['results'][0].get('txn_id', 'N/A')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text[:200])

def test_transaction_search(token):
    """Test transaction search functionality"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n2. Testing transaction search...")
    response = requests.get(
        f"{API_URL}/transactions/transactions/",
        headers=headers,
        params={
            "search": "TXN",
            "page": 1,
            "page_size": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search successful! Found {data.get('count', 0)} results")
    else:
        print(f"❌ Search failed: {response.status_code}")

def test_transaction_filters(token):
    """Test transaction filters"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n3. Testing transaction filters...")
    
    # Test status filter
    print("   a. Testing status filter (SUCCESS)...")
    response = requests.get(
        f"{API_URL}/transactions/transactions/",
        headers=headers,
        params={
            "status": "SUCCESS",
            "page": 1,
            "page_size": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status filter working! Found {data.get('count', 0)} successful transactions")
    else:
        print(f"   ❌ Status filter failed: {response.status_code}")
    
    # Test payment mode filter
    print("   b. Testing payment_mode filter (UPI)...")
    response = requests.get(
        f"{API_URL}/transactions/transactions/",
        headers=headers,
        params={
            "payment_mode": "UPI",
            "page": 1,
            "page_size": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Payment mode filter working! Found {data.get('count', 0)} UPI transactions")
    else:
        print(f"   ❌ Payment mode filter failed: {response.status_code}")
    
    # Test date range filter
    print("   c. Testing date range filter...")
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    response = requests.get(
        f"{API_URL}/transactions/transactions/",
        headers=headers,
        params={
            "date_from": date_from,
            "date_to": date_to,
            "page": 1,
            "page_size": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Date filter working! Found {data.get('count', 0)} transactions in date range")
    else:
        print(f"   ❌ Date filter failed: {response.status_code}")

def test_transaction_stats(token):
    """Test transaction statistics endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n4. Testing transaction statistics...")
    response = requests.get(
        f"{API_URL}/transactions/transactions/stats/",
        headers=headers,
        params={"range": "24h"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Stats retrieved successfully!")
        print(f"   Total transactions: {data.get('total_transactions', 0)}")
        print(f"   Total amount: ₹{data.get('total_amount', 0):,.2f}")
        print(f"   Success rate: {data.get('success_rate', 0):.1f}%")
    else:
        print(f"❌ Stats failed: {response.status_code}")

def test_transaction_analytics(token):
    """Test transaction analytics endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n5. Testing transaction analytics...")
    
    # Test payment mode distribution
    print("   a. Payment mode distribution...")
    response = requests.get(
        f"{API_URL}/transactions/analytics/",
        headers=headers,
        params={"type": "payment_modes", "range": "7d"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Payment mode analytics working! Got {len(data)} payment modes")
    else:
        print(f"   ❌ Payment mode analytics failed: {response.status_code}")
    
    # Test hourly volume
    print("   b. Hourly volume...")
    response = requests.get(
        f"{API_URL}/transactions/analytics/",
        headers=headers,
        params={"type": "hourly_volume", "hours": 24}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Hourly volume working! Got {len(data)} hours of data")
    else:
        print(f"   ❌ Hourly volume failed: {response.status_code}")
    
    # Test top clients
    print("   c. Top clients...")
    response = requests.get(
        f"{API_URL}/transactions/analytics/",
        headers=headers,
        params={"type": "top_clients", "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Top clients working! Got {len(data)} clients")
    else:
        print(f"   ❌ Top clients failed: {response.status_code}")

def test_settlement_endpoints(token):
    """Test settlement related endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n6. Testing settlement endpoints...")
    
    # Test settlement summary
    print("   a. Settlement summary...")
    response = requests.get(
        f"{API_URL}/transactions/settlements/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Settlement summary working!")
        print(f"      Pending: {data.get('pending_count', 0)} transactions, ₹{data.get('pending_amount', 0):,.2f}")
        print(f"      Settled today: {data.get('settled_today_count', 0)} transactions")
    else:
        print(f"   ❌ Settlement summary failed: {response.status_code}")
    
    # Test pending settlements
    print("   b. Pending settlements...")
    response = requests.get(
        f"{API_URL}/transactions/settlements/pending/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"   ✅ Pending settlements working! Got {len(data)} pending transactions")
        else:
            print(f"   ✅ Pending settlements working!")
    else:
        print(f"   ❌ Pending settlements failed: {response.status_code}")

def test_refund_endpoints(token):
    """Test refund related endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n7. Testing refund endpoints...")
    response = requests.get(
        f"{API_URL}/transactions/refunds/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"✅ Refunds endpoint working! Got {len(data)} refunds")
        else:
            print(f"✅ Refunds endpoint working!")
    else:
        print(f"❌ Refunds failed: {response.status_code}")

def main():
    """Run all transaction API tests"""
    print("=" * 60)
    print("TRANSACTION API INTEGRATION TEST")
    print("=" * 60)
    
    # Get authentication token
    print("\nAuthenticating...")
    token = get_auth_token()
    
    if not token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    print(f"✅ Authentication successful! Token: {token[:20]}...")
    
    # Run all tests
    test_transaction_list(token)
    test_transaction_search(token)
    test_transaction_filters(token)
    test_transaction_stats(token)
    test_transaction_analytics(token)
    test_settlement_endpoints(token)
    test_refund_endpoints(token)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()