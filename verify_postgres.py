import os
import sys
from dotenv import load_dotenv
import psycopg

load_dotenv('.env')
db_name = os.environ.get('DB_NAME', 'craftconnect_db')
user = os.environ.get('DB_USER', 'postgres')
password = os.environ.get('DB_PASSWORD', '')
host = os.environ.get('DB_HOST', '127.0.0.1')
port = os.environ.get('DB_PORT', '5432')

print(f"Checking connection to PostgreSQL at {host}:{port} as user '{user}'...")

try:
    conn = psycopg.connect(
        dbname='postgres',
        user=user,
        password=password,
        host=host,
        port=port,
        autocommit=True
    )
    print("Successfully connected to PostgreSQL server.")
    
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        exists = cur.fetchone()
        if exists:
            print(f"Database '{db_name}' already exists.")
        else:
            print(f"Database '{db_name}' does not exist yet. Creating database...")
            cur.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created successfully.")
    conn.close()

    conn_target = psycopg.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port
    )
    print(f"Successfully verified direct connection to '{db_name}'.")
    conn_target.close()
    sys.exit(0)

except psycopg.OperationalError as e:
    err_str = str(e)
    if password and password in err_str:
        err_str = err_str.replace(password, "******")
    print("PostgreSQL OperationalError:", err_str)
    sys.exit(1)
except Exception as e:
    print("Unexpected error:", type(e).__name__, str(e))
    sys.exit(2)
