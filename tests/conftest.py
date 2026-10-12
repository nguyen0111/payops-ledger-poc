import pytest
import psycopg2
from app.db import init_db
from app.config import DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS account_snapshots CASCADE")
    cursor.execute("DROP TABLE IF EXISTS ledger_entries CASCADE")
    cursor.execute("DROP TABLE IF EXISTS idempotency_keys CASCADE")
    cursor.execute("DROP TABLE IF EXISTS accounts CASCADE")
    
    conn.commit()
    conn.close()
    
    init_db()
    
    yield
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS account_snapshots CASCADE")
    cursor.execute("DROP TABLE IF EXISTS ledger_entries CASCADE")
    cursor.execute("DROP TABLE IF EXISTS idempotency_keys CASCADE")
    cursor.execute("DROP TABLE IF EXISTS accounts CASCADE")
    
    conn.commit()
    conn.close()
