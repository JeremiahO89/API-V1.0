from fastapi import APIRouter, HTTPException
from plaid.model.products import Products
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.country_code import CountryCode
from api.dependents import user_dependency
from ...plaid_client import client
from .utils import run_blocking

router = APIRouter()

# create_link_token
# generates a temp link token for the user to use in the plaid link, this allows
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
