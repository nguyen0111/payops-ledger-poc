import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from app.config import DATABASE_URL

# Thread-safe connection pool for concurrent requests
connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL
)

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key TEXT PRIMARY KEY,
            response_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id SERIAL PRIMARY KEY,
            tx_id UUID NOT NULL,
            account_id INT REFERENCES accounts(id),
            amount BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_snapshots (
            id SERIAL PRIMARY KEY,
            account_id INT REFERENCES accounts(id),
            balance_cents BIGINT NOT NULL,
            last_entry_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = connection_pool.getconn()
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)
