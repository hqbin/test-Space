import sys, logging
sys.path.insert(0, ".")
from database import engine
from api.database_admin import _split_sql_statements, _insert_data
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, force=True, stream=sys.stdout)
logger = logging.getLogger()

# Simulate a regular table (users) with different backup data
# Current DB user (id=1, name='old_user') + backup user (id=1, name='backup_user')
# Should UPDATE (not create duplicate, and not get dedup-deleted)
backup_sql = """INSERT INTO "users" ("id", "username", "email") VALUES (1, 'backup_user', 'backup@test.com');
"""
with engine.connect() as conn:
    conn.execute(text("""UPDATE users SET username='old_user', email='old@test.com' WHERE id=1"""))
    conn.commit()

count_before = 0
with engine.connect() as conn:
    r = conn.execute(text("SELECT username, email FROM users WHERE id=1")).fetchone()
    print(f"BEFORE: username={r[0]}, email={r[1]}")

statements = _split_sql_statements(backup_sql)
insert_stmts = [s for s in statements if s.upper().lstrip().startswith("INSERT")]
errors = []
task = {"progress": 0, "message": "", "executed": 0}
stats = _insert_data(logger, "dedup_regular", task, insert_stmts, errors, mode="upsert")
print(f"STATS: {stats}")

with engine.connect() as conn:
    r = conn.execute(text("SELECT username, email, count(*) FROM users WHERE id=1 GROUP BY username, email")).fetchone()
    print(f"AFTER: username={r[0]}, email={r[1]}, count={r[2]}")
