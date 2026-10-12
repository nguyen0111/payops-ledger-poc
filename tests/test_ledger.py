import pytest
from app.ledger import create_account, get_balance, create_transfer

def test_double_entry_invariant():
    alice = create_account("alice")
    bob = create_account("bob")
    
    create_transfer("deposit-001", None, alice, 10000)
    assert get_balance(alice) == 10000
    assert get_balance(bob) == 0
    
    create_transfer("transfer-001", alice, bob, 3000)
    assert get_balance(alice) == 7000
    assert get_balance(bob) == 3000
    
    total_balance = get_balance(alice) + get_balance(bob)
    assert total_balance == 10000

def test_insufficient_funds():
    alice = create_account("charlie")
    bob = create_account("dave")
    
    create_transfer("deposit-002", None, alice, 1000)
    
    with pytest.raises(ValueError, match="Insufficient funds"):
        create_transfer("transfer-002", alice, bob, 2000)
    
    assert get_balance(alice) == 1000
    assert get_balance(bob) == 0

def test_negative_amount_rejected():
    alice = create_account("eve_edge")
    bob = create_account("frank_edge")
    
    with pytest.raises(ValueError, match="Transfer amount must be strictly positive"):
        create_transfer("transfer-negative", alice, bob, -1000)
    
    with pytest.raises(ValueError, match="Transfer amount must be strictly positive"):
        create_transfer("transfer-zero", alice, bob, 0)

def test_self_transfer_rejected():
    alice = create_account("grace_edge")
    
    create_transfer("deposit-003", None, alice, 5000)
    
    with pytest.raises(ValueError, match="Cannot transfer to the same account"):
        create_transfer("self-transfer", alice, alice, 1000)
    
    assert get_balance(alice) == 5000
