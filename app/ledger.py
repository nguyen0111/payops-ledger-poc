import json
import uuid
from app.db import get_db

def get_balance(account_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT balance_cents, last_entry_id FROM account_snapshots WHERE account_id = %s ORDER BY id DESC LIMIT 1",
            (account_id,)
        )
        snapshot = cursor.fetchone()
        
        if snapshot:
            base_balance = snapshot[0]
            last_entry_id = snapshot[1]
            
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM ledger_entries WHERE account_id = %s AND id > %s",
                (account_id, last_entry_id)
            )
            delta = cursor.fetchone()[0]
            return base_balance + delta
        else:
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM ledger_entries WHERE account_id = %s",
                (account_id,)
            )
            row = cursor.fetchone()
            return row[0]

def create_transfer(idempotency_key, from_acc, to_acc, amount_cents):
    # Validate edge cases
    if amount_cents <= 0:
        raise ValueError("Transfer amount must be strictly positive")
    
    if from_acc is not None and from_acc == to_acc:
        raise ValueError("Cannot transfer to the same account")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT response_data FROM idempotency_keys WHERE key = %s", (idempotency_key,))
        existing = cursor.fetchone()
        
        if existing:
            response_data = existing[0]
            if isinstance(response_data, str):
                return json.loads(response_data)
            return response_data
        
        tx_id = str(uuid.uuid4())
        
        if from_acc is not None:
            first_lock = min(from_acc, to_acc)
            second_lock = max(from_acc, to_acc)
            
            cursor.execute("SELECT id FROM accounts WHERE id = %s FOR UPDATE", (first_lock,))
            cursor.fetchone()
            
            if first_lock != second_lock:
                cursor.execute("SELECT id FROM accounts WHERE id = %s FOR UPDATE", (second_lock,))
                cursor.fetchone()
            
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM ledger_entries WHERE account_id = %s",
                (from_acc,)
            )
            row = cursor.fetchone()
            balance = row[0]
            
            if balance < amount_cents:
                raise ValueError("Insufficient funds")
            
            cursor.execute(
                "INSERT INTO ledger_entries (tx_id, account_id, amount) VALUES (%s, %s, %s)",
                (tx_id, from_acc, -amount_cents)
            )
        
        cursor.execute(
            "INSERT INTO ledger_entries (tx_id, account_id, amount) VALUES (%s, %s, %s)",
            (tx_id, to_acc, amount_cents)
        )
        
        cursor.execute(
            "INSERT INTO idempotency_keys (key, response_data) VALUES (%s, %s)",
            (idempotency_key, json.dumps({"tx_id": tx_id, "amount": amount_cents}))
        )
        
        return {"tx_id": tx_id, "amount": amount_cents}

def create_account(name):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (name) VALUES (%s) RETURNING id", (name,))
        return cursor.fetchone()[0]

def get_account_id(name):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE name = %s", (name,))
        row = cursor.fetchone()
        return row[0] if row else None

def create_snapshot(account_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        balance = get_balance(account_id)
        
        cursor.execute(
            "SELECT MAX(id) FROM ledger_entries WHERE account_id = %s",
            (account_id,)
        )
        row = cursor.fetchone()
        last_entry_id = row[0] if row[0] else 0
        
        cursor.execute(
            "INSERT INTO account_snapshots (account_id, balance_cents, last_entry_id) VALUES (%s, %s, %s) RETURNING id",
            (account_id, balance, last_entry_id)
        )
        
        return cursor.fetchone()[0]
