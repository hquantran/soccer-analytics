import duckdb
import pathlib

p = pathlib.Path('api_sports.duckdb')
conn = duckdb.connect(str(p))
print('SHOW TABLES:', conn.execute('SHOW TABLES').fetchall())
print('ALL TABLES:', conn.execute("SELECT table_schema, table_name FROM information_schema.tables ORDER BY table_schema, table_name").fetchall())
conn.close()
