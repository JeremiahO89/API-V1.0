#routes.py
# link all of the routes together for the plaid API

from fastapi import APIRouter
from .link import router as link_router
from .tokens import router as token_router
from .transactions import router as transactions_router
from .institution import router as institution_router
from .balances import router as balances_router
from .accounts import router as plaid_accounts_router

router = APIRouter()
router.include_router(link_router, prefix="/plaid", tags=["Plaid"])
router.include_router(token_router, prefix="/plaid", tags=["Plaid"])
router.include_router(transactions_router, prefix="/plaid", tags=["Plaid"])
router.include_router(institution_router, prefix="/plaid", tags=["Plaid"])
router.include_router(balances_router, prefix="/plaid", tags=["Plaid"])
router.include_router(plaid_accounts_router, prefix="/plaid", tags=["Plaid"])