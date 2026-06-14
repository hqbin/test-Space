import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from sqlalchemy import text
from models import AmlPatch
from sqlalchemy.orm import Session

session = Session(engine)
patches = session.query(AmlPatch).limit(3).all()

for p in patches:
    print(f"ID: {p.id}, zmind_numbers raw: {p.zmind_numbers}")
    print(f"Type: {type(p.zmind_numbers)}")
    
    # Test parse function
    import json
    if isinstance(p.zmind_numbers, str):
        try:
            result = json.loads(p.zmind_numbers)
            print(f"Parsed: {result}")
        except Exception as e:
            print(f"Parse error: {e}")
    print("---")

session.close()