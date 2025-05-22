from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional
from plaid.model.transactions_get_request import TransactionsGetRequest
from api.models import PlaidAccount
from api.dependents import user_dependency, db_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter()

@router.get("/transactions")
async def get_transactions(
    current_user: user_dependency,
    db: db_dependency,
    start_date: date = Query(default=date(2024, 1, 1)),
    end_date: date = Query(default=date(2024, 12, 31)),
    plaid_account_id: Optional[int] = Query(default=None)
):
    query = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"])

    if plaid_account_id:
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
