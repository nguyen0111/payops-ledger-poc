import time
import uuid
import statistics
from psycopg2 import extras
from app.db import init_db, get_db, close_pool
from app.ledger import create_account, get_balance, create_snapshot

def calculate_percentile(data, percentile):
    """Calculate the given percentile of data."""
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1 if lower + 1 < len(sorted_data) else lower
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

def benchmark_get_balance(account_id, iterations=100):
    """Benchmark get_balance() function with given iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        get_balance(account_id)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    return times

def populate_transactions_bulk(account_id, count=20000):
    """Bulk insert N transactions using execute_values for performance."""
    print(f"Inserting {count} transactions (bulk insert)...")
    entries = []
    for _ in range(count):
        tx_id = str(uuid.uuid4())
        amount = 1000  # $10.00 in cents
        entries.append((tx_id, account_id, amount))
    
    with get_db() as conn:
        cursor = conn.cursor()
        extras.execute_values(
            cursor,
            "INSERT INTO ledger_entries (tx_id, account_id, amount) VALUES %s",
            entries
        )
        conn.commit()
    print(f"  Inserted {count} transactions completed.")

def print_benchmark_table(times_before, times_after, num_before, num_after):
    """Print a formatted ASCII comparison table."""
    avg_before = statistics.mean(times_before)
    p99_before = calculate_percentile(times_before, 99)
    avg_after = statistics.mean(times_after)
    p99_after = calculate_percentile(times_after, 99)
    
    improvement_avg = (avg_before - avg_after) / avg_before * 100
    improvement_p99 = (p99_before - p99_after) / p99_before * 100
    speedup = avg_before / avg_after
    
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Metric':<25} {'Raw SUM':<15} {'Snapshot + Delta':<20} {'Improvement':<15}")
    print("-" * 70)
    print(f"{'Transactions':<25} {num_before:<15} {num_after:<20} {'-':<15}")
    print(f"{'Average Latency':<25} {avg_before:.3f} ms     {avg_after:.3f} ms          {improvement_avg:.1f}%")
    print(f"{'P99 Latency':<25} {p99_before:.3f} ms     {p99_after:.3f} ms          {improvement_p99:.1f}%")
    print("-" * 70)
    print(f"{'Speedup Factor':<25} {'-':<15} {speedup:.2f}x          {'-':<15}")
    print("=" * 70)

def run_benchmark():
    print("=" * 70)
    print("PAYOPS LEDGER SNAPSHOT BENCHMARK")
    print("=" * 70)
    
    try:
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
        
        # Populate with 20,000 transactions using bulk insert
        num_initial = 20000
        populate_transactions_bulk(account_id, num_initial)
        
        # Verify balance
        print(f"\n2. Current balance: ${get_balance(account_id) / 100:.2f}")
        
        # Benchmark BEFORE snapshot (20,000 entries)
        print(f"\n3. Benchmarking get_balance() BEFORE snapshot (100 iterations)...")
        times_before = benchmark_get_balance(account_id, iterations=100)
        
        # Create snapshot
        print(f"\n4. Creating snapshot...")
        snapshot_id = create_snapshot(account_id)
        print(f"   Snapshot ID: {snapshot_id}")
        
        # Insert 50 delta entries after snapshot
        print(f"\n5. Inserting 50 delta entries after snapshot...")
        delta_entries = []
        for _ in range(50):
            tx_id = str(uuid.uuid4())
            amount = 1000
            delta_entries.append((tx_id, account_id, amount))
        
        with get_db() as conn:
            cursor = conn.cursor()
            extras.execute_values(
                cursor,
                "INSERT INTO ledger_entries (tx_id, account_id, amount) VALUES %s",
                delta_entries
            )
            conn.commit()
        print(f"   Inserted 50 delta entries completed.")
        
        # Benchmark AFTER snapshot (snapshot + 50 delta entries)
        print(f"\n6. Benchmarking get_balance() AFTER snapshot (100 iterations)...")
        times_after = benchmark_get_balance(account_id, iterations=100)
        
        # Print formatted table
        print_benchmark_table(times_before, times_after, num_initial, 50)
        
    finally:
        # Gracefully close connection pool
        close_pool()
        print("\nConnection pool closed gracefully.")

if __name__ == "__main__":
    run_benchmark()
