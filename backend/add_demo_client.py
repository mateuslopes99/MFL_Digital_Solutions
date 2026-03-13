import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mfl_digital.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Certificar que o banco está inicializado
import database
database.init_db()

# Make sure we don't insert duplicate
cursor.execute("SELECT id FROM clients WHERE username = 'demo'")
row = cursor.fetchone()

if not row:
    pwd = hashlib.sha256('mfl2026'.encode('utf-8')).hexdigest()
    cursor.execute("""
        INSERT INTO clients (name, niche, package, status, whatsapp_number, username, password_hash)
        VALUES ('Cliente Demo Oficial', 'Imobiliária', 'pro', 'active', '5511999999999', 'demo', ?)
    """, (pwd,))
    
    client_id = cursor.lastrowid
    
    leads_data = [
        ('5511988888881', 'João Silva', 'hot', 'compra', 'contacted'),
        ('5511988888882', 'Maria Souza', 'warm', 'aluguel', 'new'),
        ('5511988888883', 'Carlos Lima', 'cold', 'consulta', 'lost')
    ]
    
    for phone, name, classif, category, status in leads_data:
        cursor.execute("""
            INSERT INTO leads (client_id, phone, name, classification, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (client_id, phone, name, classif, category, status))

    conn.commit()
    print("Cliente 'demo' (senha: mfl2026) criado com sucesso!")
else:
    print("Cliente demo (login demo) já existe.")

conn.close()
