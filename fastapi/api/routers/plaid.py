from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date
from sqlalchemy.orm import Session
from api.models import PlaidAccount
from api.dependents import user_dependency, db_dependency
from typing import Optional

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
async def create_link_token(user: user_dependency):
    request = LinkTokenCreateRequest(
        user={"client_user_id": str(user["id"])},
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
async def exchange_token(
    request: PublicTokenRequest,
    current_user: user_dependency,
    db: db_dependency
):
    try:
        req = ItemPublicTokenExchangeRequest(public_token=request.public_token)
        response = await run_blocking(client.item_public_token_exchange, req)

        # Save access token in DB linked to the current user
        plaid_account = PlaidAccount(
            access_token=response.access_token,
            item_id=response.item_id,
            user_id=current_user["id"]
        )

        db.add(plaid_account)
        db.commit()
        db.refresh(plaid_account)

        return {"access_token": response.access_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {e}")


@router.get("/transactions")
async def get_transactions(
    current_user: user_dependency,
    db: db_dependency,
    start_date: date = Query(default=date(2024, 1, 1)),
    end_date: date = Query(default=date(2024, 12, 31)),
    plaid_account_id: Optional[int] = Query(default=None)  # optional account selector
):
    query = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"])
    
    if plaid_account_id is not None:
        plaid_account = query.filter(PlaidAccount.id == plaid_account_id).first()
        if not plaid_account:
            raise HTTPException(status_code=404, detail="Plaid account not found")
    else:
        plaid_account = query.first()
        if not plaid_account:
            raise HTTPException(status_code=404, detail="No linked Plaid accounts found")

    try:
        request = TransactionsGetRequest(
            access_token=plaid_account.access_token,
            start_date=start_date,
            end_date=end_date
        )
        response = await run_blocking(client.transactions_get, request)
        return response.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction fetch failed: {e}")

