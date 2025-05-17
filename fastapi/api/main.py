from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, user
from api.database import Base, engine

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

@app.get("/")
def api_check():
    return {"status": "API Running"}
