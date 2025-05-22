#utils.py
#This file is uesed for repeat code across the plaid routes


import asyncio
# Alows FASTAPI to run while plaid is running
def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args)