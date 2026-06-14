from database import engine, SessionLocal
from models import AmlPatch, User

session = SessionLocal()
try:
    patch = session.query(AmlPatch).filter(AmlPatch.id == 4).first()
    if patch:
        print(f"Found patch: {patch.id}")
        patch.sync_status = 2
        session.commit()
        print("Update succeeded")
except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()