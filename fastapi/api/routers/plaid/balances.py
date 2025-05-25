from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from api.models import PlaidAccount, PlaidBalance
from api.dependents import user_dependency, db_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter(prefix = "/balances")

# Fetch all balances for a user's linked Plaid accounts, from plaid only if they don't exist in the DHB
# create another git for updating the balances
@router.get("/all")
async def get_all_balances(
    current_user: user_dependency,
    db: db_dependency
):
    accounts = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"]).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No Plaid accounts linked")
    
    all_balances = []
    try:
        for plaid_account in accounts:
            # Each plaid account is the bank account linked as a whole not each individual account
            existing = db.query(PlaidBalance).filter_by(
                item_id=plaid_account.item_id,
                user_id=current_user["id"]
            ).all()
            if existing:
                for acct in existing:
                    all_balances.append({
                        "account_id": acct.account_id,
                        "item_id": acct.item_id,
                        "name": acct.name,
                        "type": acct.type,
                        "subtype": acct.subtype,
                        "available": acct.available,
                        "current": acct.current,
                        "limit": acct.limit,
                        "last_updated": acct.last_updated  # fixed field name
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Balance fetch failed for account {plaid_account.id}: {e}")

    return all_balances


@router.post("/update_all")
async def update_all_balances(
    current_user: user_dependency,
    db: db_dependency,
    force: bool = False
):
    accounts = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"]).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No Plaid accounts linked")
    errors = []
    for plaid_account in accounts:
        try:
            existing = db.query(PlaidBalance).filter_by(
                item_id=plaid_account.item_id,
                user_id=current_user["id"]
            ).all()
            
            current_time = datetime.now(timezone.utc)
            needs_update = ( force or not existing or (existing and (current_time - existing[0].last_updated).total_seconds() > 86400))
            if needs_update:
                await update_balance(current_user, db, plaid_account)
        except Exception as e:
            errors.append(f"Balance update failed for account {plaid_account.id}: {e}")
    db.commit()  # Batch commit after all updates

    if errors:
        # Log errors, but don't fail the whole request
        return {"status": "partial", "errors": errors}
    return {"status": "success"}

async def update_balance(user: user_dependency, db: db_dependency, plaid_account: PlaidAccount):
    request = AccountsBalanceGetRequest(access_token=plaid_account.access_token)
    response = await run_blocking(client.accounts_balance_get, request)
    for account_balance in response.accounts:
        existing = db.query(PlaidBalance).filter_by(
            account_id=account_balance.account_id,
            item_id=plaid_account.item_id,
            user_id=user["id"]
        ).first()
        
         # Get enum values as strings
        type_str = account_balance.type.value if hasattr(account_balance.type, "value") else account_balance.type
        subtype_str = account_balance.subtype.value if hasattr(account_balance.subtype, "value") else account_balance.subtype
        
        if existing:
            existing.available = account_balance.balances.available
            existing.current = account_balance.balances.current
            existing.limit = account_balance.balances.limit
            existing.last_updated = datetime.now(timezone.utc)
        else:
            new_balance = PlaidBalance(
                account_id=account_balance.account_id,
                item_id=plaid_account.item_id,
                user_id=user["id"],
                name=account_balance.name,
                type=type_str, 
                subtype=subtype_str,
                available=account_balance.balances.available,
                current=account_balance.balances.current,
                limit=account_balance.balances.limit,
                last_updated=datetime.now(timezone.utc)
            )
            db.add(new_balance)