import pytest
import threading
from app.ledger import create_account, get_balance, create_transfer

def test_concurrent_transfers_no_double_spend():
    alice = create_account("eve")
    bob = create_account("frank")
    
    initial_balance = 10000
    create_transfer("deposit-concurrent-001", None, alice, initial_balance)
    
    transfer_amount = 1000
    num_threads = 20
    success_count = 0
    fail_count = 0
    
    def worker(thread_id):
        nonlocal success_count, fail_count
        try:
            create_transfer(f"transfer-concurrent-{thread_id}", alice, bob, transfer_amount)
            success_count += 1
        except ValueError:
            fail_count += 1
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    final_balance = get_balance(alice)
    
    assert success_count == 10, f"Expected exactly 10 successful transfers, got {success_count}"
    assert fail_count == 10, f"Expected exactly 10 failed transfers, got {fail_count}"
    assert final_balance == 0, f"Expected final balance of 0, got {final_balance}"

def test_cross_transfer_deadlock_prevention():
    alice = create_account("grace")
    bob = create_account("heidi")
    
    create_transfer("deposit-grace", None, alice, 5000)
    create_transfer("deposit-heidi", None, bob, 5000)
    
    success_count = 0
    
    def alice_to_bob():
        nonlocal success_count
        try:
            create_transfer("cross-a2b", alice, bob, 1000)
            success_count += 1
        except ValueError:
            pass
    
    def bob_to_alice():
        nonlocal success_count
        try:
            create_transfer("cross-b2a", bob, alice, 1000)
            success_count += 1
        except ValueError:
            pass
    
    t1 = threading.Thread(target=alice_to_bob)
    t2 = threading.Thread(target=bob_to_alice)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    assert success_count == 2, "Both cross-transfers should succeed without deadlock"
