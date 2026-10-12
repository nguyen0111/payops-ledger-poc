# PayOps Platform (Core Ledger & Reconciliation POC)

A learning PoC exploring financial ledger immutability, concurrency locking (PostgreSQL SELECT ... FOR UPDATE), and streaming bank reconciliation.

## Problem Statement

Naive balance updates fail under concurrent load. If two requests simultaneously read a balance of $100 and both deduct $50, the account ends at $0 instead of -$50 (double-spending). This POC demonstrates how immutable double-entry ledgers and database-level row locking solve this problem.

## Key Mechanics

### 1. Deterministic Row Locking with Postgres `SELECT FOR UPDATE`

To prevent TOCTOU (Time-of-Check-Time-of-Use) race conditions, transfers lock accounts at the database level:

```sql
BEGIN;
SELECT id FROM accounts WHERE id = 1 FOR UPDATE;  -- Lock account 1
SELECT COALESCE(SUM(amount), 0) FROM ledger_entries WHERE account_id = 1;
-- Check balance, insert entries, commit
```

Lock ordering is deterministic (always lock `min(from_acc, to_acc)` before `max(from_acc, to_acc)`) to prevent deadlocks when Alice and Bob transfer to each other simultaneously.

### 2. Balance Snapshotting

`SELECT SUM(amount)` on a table with 500K+ transactions becomes slow. Snapshots store cumulative balance and the highest entry ID:

```sql
balance = snapshot.balance_cents + SUM(entries WHERE id > snapshot.last_entry_id)
```

This reduces balance queries from O(N) to O(k) where k = new transactions since last snapshot.

**Benchmark Results (20,000 transactions):**
- Before snapshot: 7.352 ms average
- After snapshot: 5.483 ms average
- Improvement: 25.4% faster (1.3x speedup)

Run benchmark: `PYTHONPATH=. python scripts/benchmark.py`

### 3. Reconciliation Strategy

The reconciliation engine streams bank CSV files line-by-line to handle large datasets. For this PoC, internal ledger entries are batch-mapped in memory for simplicity. In an enterprise setup, this would be executed via a SQL FULL OUTER JOIN against a temporary bank staging table to avoid loading large datasets into application memory.

## Quickstart

### Prerequisites

- Python 3.9+
- PostgreSQL 18 (running locally)

### Setup

```bash
# Install PostgreSQL via Homebrew (macOS)
brew install postgresql@18
brew services start postgresql@18

# Create database
createdb payops_db

# Copy environment configuration
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v

# Start server
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /api/v1/transfers` - Execute transfer with idempotency key
- `GET /api/v1/accounts/{account_id}/balance` - Get account balance
- `POST /api/v1/accounts/{account_id}/snapshot` - Create balance snapshot
- `POST /api/v1/reconcile` - Run bank reconciliation

## Financial Core Rules

- Amounts stored as integers in cents (1000 = $10.00)
- Ledger is append-only (no UPDATE/DELETE on transactions)
- Double-entry invariant: total system balance always conserved
