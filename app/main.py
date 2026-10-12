from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.ledger import create_transfer, get_balance, create_snapshot
from app.reconcile import generate_mock_bank_statement, run_reconciliation

app = FastAPI()

class TransferRequest(BaseModel):
    from_acc: Optional[int] = None
    to_acc: int
    amount_cents: int

@app.post("/api/v1/transfers")
def transfer(request: TransferRequest, idempotency_key: str = Header(..., alias="Idempotency-Key")):
    try:
        result = create_transfer(idempotency_key, request.from_acc, request.to_acc, request.amount_cents)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})

@app.get("/api/v1/accounts/{account_id}/balance")
def get_account_balance(account_id: int):
    balance = get_balance(account_id)
    return {"account_id": account_id, "balance_cents": balance}

@app.post("/api/v1/accounts/{account_id}/snapshot")
def create_account_snapshot(account_id: int):
    snapshot_id = create_snapshot(account_id)
    return {"account_id": account_id, "snapshot_id": snapshot_id}

@app.post("/api/v1/reconcile")
def reconcile(csv_filepath: str = "bank_statement.csv"):
    generate_mock_bank_statement(csv_filepath)
    result = run_reconciliation(csv_filepath)
    return result
