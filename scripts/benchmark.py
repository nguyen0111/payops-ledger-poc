import time
import uuid
from app.db import init_db, get_db
from app.ledger import create_account, get_balance, create_transfer, create_snapshot, get_account_id

def benchmark_get_balance(account_id, iterations=100):
    """Benchmark get_balance() function with given iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        get_balance(account_id)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    return times

def populate_transactions(account_id, count=20000):
    """Insert N transactions into the ledger."""
    print(f"Inserting {count} transactions...")
    with get_db() as conn:
        cursor = conn.cursor()
        for i in range(count):
            tx_id = str(uuid.uuid4())
            amount = 1000  # $10.00 in cents
            cursor.execute(
                "INSERT INTO ledger_entries (tx_id, account_id, amount) VALUES (%s, %s, %s)",
                (tx_id, account_id, amount)
            )
            if i % 5000 == 0:
                print(f"  Inserted {i} transactions...")
        conn.commit()
    print(f"  Inserted {count} transactions completed.")

def run_benchmark():
    print("=" * 60)
    print("PAYOPS LEDGER SNAPSHOT BENCHMARK")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Clean up any existing benchmark account
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ledger_entries WHERE account_id IN (SELECT id FROM accounts WHERE name = 'benchmark_account')")
        cursor.execute("DELETE FROM account_snapshots WHERE account_id IN (SELECT id FROM accounts WHERE name = 'benchmark_account')")
        cursor.execute("DELETE FROM accounts WHERE name = 'benchmark_account'")
        conn.commit()
    
    # Create benchmark account
    print("\n1. Creating benchmark account...")
    account_id = create_account("benchmark_account")
    print(f"   Account ID: {account_id}")
    
    # Populate with transactions
    num_transactions = 20000
    populate_transactions(account_id, num_transactions)
    
    # Verify balance
    print(f"\n2. Current balance: ${get_balance(account_id) / 100:.2f}")
    
    # Benchmark BEFORE snapshot
    print(f"\n3. Benchmarking get_balance() BEFORE snapshot (100 iterations)...")
    times_before = benchmark_get_balance(account_id, iterations=100)
    avg_before = sum(times_before) / len(times_before)
    min_before = min(times_before)
    max_before = max(times_before)
    print(f"   Average: {avg_before:.3f} ms")
    print(f"   Min:     {min_before:.3f} ms")
    print(f"   Max:     {max_before:.3f} ms")
    
    # Create snapshot
    print(f"\n4. Creating snapshot...")
    snapshot_id = create_snapshot(account_id)
    print(f"   Snapshot ID: {snapshot_id}")
    
    # Benchmark AFTER snapshot
    print(f"\n5. Benchmarking get_balance() AFTER snapshot (100 iterations)...")
    times_after = benchmark_get_balance(account_id, iterations=100)
    avg_after = sum(times_after) / len(times_after)
    min_after = min(times_after)
    max_after = max(times_after)
    print(f"   Average: {avg_after:.3f} ms")
    print(f"   Min:     {min_after:.3f} ms")
    print(f"   Max:     {max_after:.3f} ms")
    
    # Calculate improvement
    improvement = (avg_before - avg_after) / avg_before * 100
    speedup = avg_before / avg_after
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Transaction count: {num_transactions}")
    print(f"Before snapshot:    {avg_before:.3f} ms avg")
    print(f"After snapshot:     {avg_after:.3f} ms avg")
    print(f"Improvement:        {improvement:.1f}%")
    print(f"Speedup:            {speedup:.1f}x faster")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
