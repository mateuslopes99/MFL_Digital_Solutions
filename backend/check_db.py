from database import get_connection
conn = get_connection()
cur  = conn.cursor()
cur.execute('SELECT id, name, package, status FROM clients')
clients = cur.fetchall()
if clients:
    for c in clients:
        print(f'  ID={c["id"]} | {c["name"]} | {c["package"]} | {c["status"]}')
else:
    print('  Banco sem clientes reais ainda (dados demo estao no frontend)')
cur.execute('SELECT COUNT(*) as n FROM leads')
print(f'  Leads no banco: {cur.fetchone()["n"]}')
conn.close()
