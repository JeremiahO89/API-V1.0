from fastapi import APIRouter, HTTPException
from api.dependents import user_dependency, db_dependency
from api.models import PlaidAccount

router = APIRouter(prefix="/accounts")

@router.get("/all")
async def get_all_accounts(
    current_user: user_dependency,
    db: db_dependency
):
    accounts = db.query(PlaidAccount).filter(PlaidAccount.user_id == current_user["id"]).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No Plaid accounts linked")
    
    all_accounts = []
    for plaid_account in accounts:
        try:
            all_accounts.append({
                "id": plaid_account.id,
                "item_id": plaid_account.item_id,
                "institution_id": plaid_account.institution_id,
                "created_at": plaid_account.created_at.isoformat(),
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch account {plaid_account.id}: {e}")
    
    return all_accounts