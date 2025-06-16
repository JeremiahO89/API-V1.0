from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
import os
from dotenv import load_dotenv

load_dotenv()
#env = os.getenv("PLAID_ENV", "sandbox").lower()
env = os.getenv("PLAID_ENV").lower()

host_map = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

configuration = Configuration(
    host=host_map[env],
)
configuration.api_key["clientId"] = os.getenv("PLAID_CLIENT_ID")
configuration.api_key["secret"] = os.getenv("PLAID_SECRET")

client = plaid_api.PlaidApi(ApiClient(configuration))


# print("Plaid Environment:", env)
# print("Client ID:", configuration.api_key['clientId'])
# print("Secret:", configuration.api_key['secret'])