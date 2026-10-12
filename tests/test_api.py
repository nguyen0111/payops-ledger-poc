import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ledger import create_account, get_balance, create_transfer

client = TestClient(app)

def test_transfer_endpoint():
    alice = create_account("leo")
    bob = create_account("mia")
    
    create_transfer("deposit-api-001", None, alice, 10000)
    
    response = client.post(
        "/api/v1/transfers",
        json={"from_acc": alice, "to_acc": bob, "amount_cents": 3000},
        headers={"Idempotency-Key": "transfer-api-001"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "tx_id" in data
    assert data["amount"] == 3000

def test_idempotency_key_replay():
    alice = create_account("nora")
    bob = create_account("oscar")
    
    create_transfer("deposit-api-002", None, alice, 5000)
    
    response1 = client.post(
        "/api/v1/transfers",
        json={"from_acc": alice, "to_acc": bob, "amount_cents": 1000},
        headers={"Idempotency-Key": "transfer-api-002"}
    )
    
    response2 = client.post(
        "/api/v1/transfers",
        json={"from_acc": alice, "to_acc": bob, "amount_cents": 1000},
        headers={"Idempotency-Key": "transfer-api-002"}
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()
    
    assert get_balance(alice) == 4000
    assert get_balance(bob) == 1000

def test_insufficient_funds_api():
    alice = create_account("paul")
    bob = create_account("quinn")
    
    create_transfer("deposit-api-003", None, alice, 1000)
    
    response = client.post(
        "/api/v1/transfers",
        json={"from_acc": alice, "to_acc": bob, "amount_cents": 2000},
        headers={"Idempotency-Key": "transfer-api-003"}
    )
    
    assert response.status_code == 400
    assert "error" in response.json()["detail"]

def test_get_balance_endpoint():
    account = create_account("rachel")
    create_transfer("deposit-api-004", None, account, 7500)
    
    response = client.get(f"/api/v1/accounts/{account}/balance")
    
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == account
    assert data["balance_cents"] == 7500

def test_create_snapshot_endpoint():
    account = create_account("sam")
    create_transfer("deposit-api-005", None, account, 3000)
    
    response = client.post(f"/api/v1/accounts/{account}/snapshot")
    
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == account
    assert "snapshot_id" in data
