import csv
import uuid
import random
from app.db import get_db

def generate_mock_bank_statement(csv_filename="bank_statement.csv"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tx_id, amount FROM ledger_entries WHERE amount > 0 ORDER BY id DESC LIMIT 20"
        )
        entries = cursor.fetchall()
    
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_id", "bank_amount_cents", "status"])
        
        for entry in entries:
            tx_id = entry[0]
            amount = entry[1]
            
            rand = random.random()
            if rand < 0.8:
                bank_amount = amount
            elif rand < 0.9:
                bank_amount = amount - 150
            else:
                tx_id = str(uuid.uuid4())
                bank_amount = amount
            
            writer.writerow([tx_id, bank_amount, "settled"])

def run_reconciliation(csv_filepath):
    matched = []
    fee_discrepancy = []
    unmatched_ghost = []
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tx_id, amount FROM ledger_entries WHERE amount > 0")
        internal_entries = {row[0]: row[1] for row in cursor.fetchall()}
    
    with open(csv_filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tx_id = row["tx_id"]
            bank_amount = int(row["bank_amount_cents"])
            
            if tx_id in internal_entries:
                internal_amount = internal_entries[tx_id]
                if internal_amount == bank_amount:
                    matched.append({"tx_id": tx_id, "amount": bank_amount})
                else:
                    fee_discrepancy.append({
                        "tx_id": tx_id,
                        "internal_amount": internal_amount,
                        "bank_amount": bank_amount,
                        "diff": internal_amount - bank_amount
                    })
            else:
                unmatched_ghost.append({"tx_id": tx_id, "bank_amount": bank_amount})
    
    return {
        "matched_count": len(matched),
        "fee_discrepancy_count": len(fee_discrepancy),
        "unmatched_ghost_count": len(unmatched_ghost),
        "matched": matched,
        "fee_discrepancy": fee_discrepancy,
        "unmatched_ghost": unmatched_ghost
    }
