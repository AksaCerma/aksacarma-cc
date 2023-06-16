import os

import async_cse
from dotenv import load_dotenv
from os.path import isfile

if isfile(".env"):
    load_dotenv()

api_keys = [os.getenv(f"GOOGLE_KEY_{i}") for i in range(1, 6)]
google_client = async_cse.Search(api_keys)


async def get_google_result(prediction):
    try:
        results = await google_client.search(prediction)
    except:
        results = []

    return [
        {
            "title": result.title,
            "url": result.url,
            "description": result.description,
            "image_url": result.image_url,
        }
        for result in results
    ]
