# Asynchronous TestRail API for Python
Modified official TestRail library to work asynchronously using `aiohttp`.
Requires minimum modifications to start running code asynchronously. Greatly speeding up endpoints that can't be "multi queried" e.g. /get_cases/ for multiple sections.
Contains the original synchronous methods as well.


## Example
```python
from aiotestrail import APIClient
import asyncio
import aiohttp

''' # I recommend running a .env config file
import os
from dotenv import load_dotenv

URL = os.getenv("URL")
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
'''

client = APIClient(URL)
client.user = LOGIN
client.password = PASSWORD

PROJECT_ID = 1

# OLD synchronous method example
def get_section_ids(suite_id):
    section_ids_list = [123456, 987654, 146808]

    sections = client.send_get(f"/get_sections/{PROJECT_ID}&suite_id={suite_id}")
    for section in sections:
        section_ids_list.append(section['id'])

    return section_ids_list

# NEW asynchronous example
async def get_cases(suite_id, section_id, session):
    cases = await client.send_get_async(f"/get_cases/{PROJECT_ID}&suite_id={suite_id}&section_id={section_id}", session=session)
    return cases

async def fetch_cases(suite_id, section_ids_list):
    async with aiohttp.ClientSession() as session:
        coroutines = (get_cases(suite_id, section_id, session=session) for section_id in section_ids_list)
        return await asyncio.gather(*coroutines)


suite_id = 97531
section_ids = get_section_ids(suite_id)

asyncio.run(fetch_cases(suite_id, section_ids))
```
Make sure to follow the API limits.
