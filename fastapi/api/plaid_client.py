from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv("PLAID_ENV", "sandbox").lower()

host_map = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

configuration = Configuration(
    host=host_map.get(env, "https://sandbox.plaid.com"),
    api_key={
        'client_id': os.getenv("PLAID_CLIENT_ID"),  # use snake_case here!
        'secret': os.getenv("PLAID_SECRET"),
    }
)

api_client = plaid_api.PlaidApi(ApiClient(configuration))
