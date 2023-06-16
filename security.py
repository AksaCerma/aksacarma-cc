import os

from dotenv import load_dotenv
from os.path import isfile
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.exceptions import HTTPException
import jwt

if isfile(".env"):
    load_dotenv()

bearer_scheme = HTTPBearer()


async def validate_credential(api_key=Header(None)):
    if api_key != os.getenv("SECRET_KEY"):
        raise HTTPException(401, "Invalid authentication credentials")


async def validate_token(token=Header(None)):
    if token:
        try:
            token = jwt.decode(token, os.getenv("SECRET_KEY"), "HS256")
        except Exception as e:
            token = None

    return token
