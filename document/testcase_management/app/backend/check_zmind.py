from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, zmind_numbers FROM aml_patches LIMIT 5")).fetchall()
    for r in result:
        print(f"ID: {r[0]}, zmind_numbers: {r[1]}")