from fastapi import APIRouter, HTTPException
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from api.models import PlaidAccount, PlaidBalance
from api.dependents import user_dependency, db_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter()

@router.get("/balances")
async def get_all_balances(
    current_user: user_dependency,
    db: db_dependency
):
    accounts = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"]).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No Plaid accounts linked")

    all_balances = []

    for plaid_account in accounts:
        try:
            request = AccountsBalanceGetRequest(access_token=plaid_account.access_token)
            response = await run_blocking(client.accounts_balance_get, request)

            for acct in response.accounts:
                # Store or update PlaidBalance
                existing = db.query(PlaidBalance).filter_by(
                    account_id=acct.account_id,
                    user_id=current_user["id"]
                ).first()

                if existing:
                    existing.name = acct.name
                    existing.type = acct.type
                    existing.subtype = acct.subtype
                    existing.available = acct.balances.available
                    existing.current = acct.balances.current
                    existing.limit = acct.balances.limit
                else:
                    new_balance = PlaidBalance(
                        account_id=acct.account_id,
                        user_id=current_user["id"],
                        name=acct.name,
                        type=acct.type,
                        subtype=acct.subtype,
                        available=acct.balances.available,
                        current=acct.balances.current,
                        limit=acct.balances.limit
                    )
                    db.add(new_balance)

                # Attach institution_id for response
                all_balances.append({
                    "institution_id": plaid_account.institution_id,
                    "account_id": acct.account_id,
                    "name": acct.name,
                    "type": acct.type,
                    "subtype": acct.subtype,
                    "available": acct.balances.available,
                    "current": acct.balances.current,
                    "limit": acct.balances.limit
                })

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Balance fetch failed for account {plaid_account.id}: {e}")

    db.commit()
    return all_balances
