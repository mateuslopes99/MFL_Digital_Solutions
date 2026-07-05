import psycopg2, os

DATABASE_URL = "postgresql://neondb_owner:npg_AoTeDdPjJL70@ep-holy-forest-at92x1f7-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]
print("Tabelas no Neon:")
for t in tables:
    print(f"  OK: {t}")
print(f"\nTotal: {len(tables)} tabelas")
conn.close()
