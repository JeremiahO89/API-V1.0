from fastapi import APIRouter, HTTPException
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from api.models import PlaidAccount, PlaidBalance
from api.dependents import user_dependency, db_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter()

# Fetch all balances for a user's linked Plaid accounts, from plaid only if they don't exist in the DHB
# create another git for updating the balances
@router.get("/balances")
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
                    all_balances.append(acct)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Balance fetch failed for account {plaid_account.id}: {e}")

    return all_balances




                # try:
                #     request = AccountsBalanceGetRequest(access_token=plaid_account.access_token)
                #     response = await run_blocking(client.accounts_balance_get, request)
                #     for acct in response.accounts: # Bank can have multiple accounts Savings, Checking, etc
                #         existing = db.query(PlaidBalance).filter_by(
                #             account_id=acct.item_id,
                #             user_id=current_user["id"]
                #         ).first()

                #         if existing: # checks if the account already exists in the DB
                #             existing.name = acct.name
                #             existing.type = acct.type
                #             existing.subtype = acct.subtype
                #             existing.available = acct.balances.available
                #             existing.current = acct.balances.current
                #             existing.limit = acct.balances.limit
                #         else:
                #             new_balance = PlaidBalance(
                #                 account_id=acct.account_id,
                #                 user_id=current_user["id"],
                #                 name=acct.name,
                #                 type=acct.type,
                #                 subtype=acct.subtype,
                #                 available=acct.balances.available,
                #                 current=acct.balances.current,
                #                 limit=acct.balances.limit
                #             )
                #             db.add(new_balance)


                #         # Attach institution_id for response
                #         all_balances.append({
                #             "institution_id": plaid_account.institution_id,
                #             "account_id": acct.account_id,
                #             "name": acct.name,
                #             "type": acct.type,
                #             "subtype": acct.subtype,
                #             "available": acct.balances.available,
                #             "current": acct.balances.current,
                #             "limit": acct.balances.limit
                #         })
                #     db.commit()
