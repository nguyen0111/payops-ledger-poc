import pytest
from app.ledger import create_account, get_balance, create_transfer, create_snapshot

def test_snapshot_balance_accuracy():
    alice = create_account("ivan")
    bob = create_account("judy")
    
    create_transfer("deposit-snapshot-001", None, alice, 10000)
    create_transfer("transfer-snapshot-001", alice, bob, 3000)
    
    balance_before_snapshot = get_balance(alice)
    assert balance_before_snapshot == 7000
    
    snapshot_id = create_snapshot(alice)
    assert snapshot_id > 0
    
    balance_after_snapshot = get_balance(alice)
    assert balance_after_snapshot == balance_before_snapshot
    
    create_transfer("transfer-snapshot-002", alice, bob, 2000)
    
    final_balance = get_balance(alice)
    assert final_balance == 5000

def test_snapshot_with_no_transactions():
    account = create_account("karen")
    
    balance = get_balance(account)
    assert balance == 0
    
    snapshot_id = create_snapshot(account)
    assert snapshot_id > 0
    
    balance_after = get_balance(account)
    assert balance_after == 0
