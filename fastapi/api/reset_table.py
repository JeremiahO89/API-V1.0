from fastapi.api.database import Base, engine
from fastapi.api.models import PlaidAccount

# Drop the specific table
PlaidAccount.__table__.drop(engine)

# Recreate the table with the new column
Base.metadata.create_all(bind=engine)

print("✅ Table reset successfully.")
