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
                        "last_updated": acct.last_updated.isoformat() + "Z" if acct.last_updated else None
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
    
    with open("debug_log.txt", "a") as f:
                    f.write(f"Call Ran")
                    
                    
    accounts = db.query(PlaidAccount).filter(
        PlaidAccount.user_id == current_user["id"]
    ).all()

    if not accounts:
        raise HTTPException(status_code=404, detail="No Plaid accounts linked")

    errors = []

    for plaid_account in accounts:
        try:
            existing = db.query(PlaidBalance).filter_by(
                item_id=plaid_account.item_id,
                user_id=current_user["id"]
            ).first()
        
            now = datetime.now(timezone.utc)
            
            if existing:
                existing_last_updated = existing.last_updated
                if existing_last_updated.tzinfo is None:
                    existing_last_updated = existing_last_updated.replace(tzinfo=timezone.utc)
                time_needs_update = (now - existing_last_updated).total_seconds() > 3600  # allows update every hour
            else:
                time_needs_update = True  # no existing means we should update

            needs_update = (force or time_needs_update)
                
            if needs_update:
                await update_balance(current_user, db, plaid_account)
                db.flush()  # Flush after each successful update
        except Exception as e:
            print(f"Error updating balance for account {plaid_account.id}: {e}")
            db.rollback()  # Roll back any partial state from this account
            errors.append(f"Balance update failed for account {plaid_account.id}: {e}")

    try:
        db.commit()  # Commit once after all updates
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Commit failed: {e}")

    if errors:
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

        type_str = getattr(account_balance.type, "value", account_balance.type)
        subtype_str = getattr(account_balance.subtype, "value", account_balance.subtype)

        if existing:
            # Update existing balance
            existing.name = account_balance.name
            existing.type = type_str
            existing.subtype = subtype_str
            existing.available = account_balance.balances.available
            existing.current = account_balance.balances.current
            existing.limit = account_balance.balances.limit
            existing.last_updated = datetime.now(timezone.utc)
        else:
            # Add new balance
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
            
            
@router.delete("/clear_balances")
def clear_balances(db: db_dependency):
    db.query(PlaidBalance).delete()
    db.commit()
    return {"status": "success", "message": "All balances deleted"}