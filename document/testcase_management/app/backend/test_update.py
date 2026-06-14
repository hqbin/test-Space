from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if sync_status column exists
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'aml_patches' AND column_name = 'sync_status'")).fetchone()
    if result:
        print("sync_status column exists")
    else:
        print("sync_status column does NOT exist")
    
    # Try updating a record
    try:
        conn.execute(text("UPDATE aml_patches SET sync_status = 2 WHERE id = 4"))
        conn.commit()
        print("Update succeeded")
    except Exception as e:
        print(f"Update failed: {e}")