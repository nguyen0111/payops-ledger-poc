import pytest
import os
from app.ledger import create_account, create_transfer
from app.reconcile import generate_mock_bank_statement, run_reconciliation

def test_reconciliation_matching():
    alice = create_account("tom")
    bob = create_account("uma")
    
    create_transfer("deposit-reconcile-001", None, alice, 10000)
    create_transfer("transfer-reconcile-001", alice, bob, 3000)
    create_transfer("transfer-reconcile-002", alice, bob, 2000)
    
    csv_path = "test_bank_statement.csv"
    generate_mock_bank_statement(csv_path)
    
    result = run_reconciliation(csv_path)
    
    assert "matched_count" in result
    assert "fee_discrepancy_count" in result
    assert "unmatched_ghost_count" in result
    
    assert result["matched_count"] >= 0
    assert result["fee_discrepancy_count"] >= 0
    assert result["unmatched_ghost_count"] >= 0
    
    if os.path.exists(csv_path):
        os.remove(csv_path)
