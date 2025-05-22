#plaid.py
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from plaid.model.products import Products
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from ..plaid_client import client
from pydantic import BaseModel
import asyncio

router = APIRouter(
    prefix="/plaid",
    tags=["plaid"]
)

# Run sync Plaid client methods without blocking FastAPI's event loop
def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args)

# POST /create_link_token
@router.post("/create_link_token")
async def create_link_token(user_id: str = "user_good"):  # Replace with real auth
    request = LinkTokenCreateRequest(
        user={"client_user_id": user_id},
        client_name="My App",
        products=[Products("auth"), Products("transactions")],
        country_codes=[CountryCode('US')],
        language='en'
    )
    try:
        response = await run_blocking(client.link_token_create, request)
        return {"link_token": response.link_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plaid error: {e}")

# Request model for public token
class PublicTokenRequest(BaseModel):
    public_token: str

# POST /exchange_public_token
@router.post("/exchange_public_token")
async def exchange_token(request: PublicTokenRequest):
    try:
        req = ItemPublicTokenExchangeRequest(public_token=request.public_token)
        response = await run_blocking(client.item_public_token_exchange, req)
        return {"access_token": response.access_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {e}")

# GET /transactions
@router.get("/transactions")
async def get_transactions(
    access_token: str,
    start_date: date = Query(default=date(2024, 1, 1)),
    end_date: date = Query(default=date(2024, 12, 31))
):
    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        response = await run_blocking(client.transactions_get, request)
        return response.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction fetch failed: {e}")
