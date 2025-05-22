from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_get_request import ItemGetRequest
from api.models import PlaidAccount
from api.dependents import user_dependency, db_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter()

class PublicTokenRequest(BaseModel):
    public_token: str

@router.post("/exchange_public_token")
async def exchange_token(
    request: PublicTokenRequest,
    current_user: user_dependency,
    db: db_dependency
):
    try:
        req = ItemPublicTokenExchangeRequest(public_token=request.public_token)
        response = await run_blocking(client.item_public_token_exchange, req)
        item_req = ItemGetRequest(access_token=response.access_token)
        item_response = await run_blocking(client.item_get, item_req)
        # Save access token in DB, while checking if this users bank account is already linked
        existing = db.query(PlaidAccount).filter(
            PlaidAccount.user_id == current_user["id"],
            PlaidAccount.institution_id == item_response.item.institution_id
        ).first()

        if existing:
            existing.access_token = response.access_token
            db.commit()
        else:
            plaid_account = PlaidAccount(
                access_token=response.access_token,
                item_id=response.item_id,
                user_id=current_user["id"],
                institution_id=item_response.item.institution_id
            )
            db.add(plaid_account)
            db.commit()
            db.refresh(plaid_account)

        
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {e}")
