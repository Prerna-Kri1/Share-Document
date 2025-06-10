from fastapi import FastAPI
from app.routes.documents_routes import documents_router
from app.database import Base, engine
from app.routes.auth import auth_router  

app=FastAPI()


Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

app.include_router(documents_router)

