import csv
import json
import random
import os
from datetime import datetime, timedelta

def generate_mock_data():
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # ---------------------------------------------------------
    # 1. CREATE CSV: Customers Data
    # ---------------------------------------------------------
    csv_file = "data/customers.csv"
    headers = ["customer_id", "first_name", "last_name", "email", "created_at"]
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        for i in range(1, 101): # 100 customers
            # Intentional Error: 5% chance of a malformed email (missing '@')
            email = f"user{i}@example.com" if random.random() > 0.05 else f"user{i}example.com"
            
            # Intentional Error: 5% chance of missing first name
            first_name = f"First{i}" if random.random() > 0.05 else ""
            
            # Random date within the last year
            created_at = (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
            
            writer.writerow([i, first_name, f"Last{i}", email, created_at])
            
    print(f"✅ Created CSV: {csv_file} (100 records)")

    # ---------------------------------------------------------
    # 2. CREATE JSON: Sales Data
    # ---------------------------------------------------------
    json_file = "data/sales.json"
    sales_data = []
    
    for i in range(1, 301): # 300 sales
        # Intentional Error: 5% chance of negative sale amount
        amount = round(random.uniform(-50.0, 500.0) if random.random() < 0.05 else random.uniform(5.0, 500.0), 2)
        
        # Intentional Error: 5% chance of unsupported currency
        currency = random.choice(["USD", "EUR", "CAD"]) if random.random() > 0.05 else "GBP"
        
        # Random date within the last 30 days
        ts = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        
        sales_data.append({
            "sale_id": i,
            "customer_id": random.randint(1, 100), # Maps back to customer_id in the CSV
            "amount": amount,
            "currency": currency,
            "ts": ts
        })
        
    with open(json_file, mode="w", encoding="utf-8") as file:
        json.dump(sales_data, file, indent=4)
        
    print(f"✅ Created JSON: {json_file} (300 records)")

if __name__ == "__main__":
    generate_mock_data()
