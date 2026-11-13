# backend/create_tables.py  (dev uniquement ; en production utilise Alembic)
from database import Base, engine
import models  # noqa: F401  (enregistre les tables)

Base.metadata.create_all(bind=engine)
print("Tables created:", ", ".join(Base.metadata.tables))
