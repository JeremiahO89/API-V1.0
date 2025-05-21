from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, user, transaction, plaid
from api.database import Base, engine
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(transaction.router)
app.include_router(plaid.router)


@app.get("/")
def api_check():
    return {"status": "API Running"}
