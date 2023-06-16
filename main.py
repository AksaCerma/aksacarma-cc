import datetime
import hashlib
import os
import uuid
from typing import List
from os.path import isfile
from zipfile import ZipFile
from ast import literal_eval

import aiomysql
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, RedirectResponse
from uvicorn import run
from google.cloud import storage

from google_search import get_google_result
from models import (
    HistoryResponse,
    LoginResponse,
    PredictionResponse,
    RegisterResponse,
    UpdateResponse,
    UserResponse,
)
from security import validate_credential, validate_token
from skin_detect import detect_skin_image

if isfile(".env"):
    load_dotenv()

# if not isfile("aksacarma-2e5f57e8e8c5.json"):
#     with ZipFile("aksacarma_cloud_storage_sa_a850f4.zip", "r") as sa_key:
#         sa_key.extractall(pwd=os.getenv("ZIP_PASS").encode())

gcs_client = None

if os.getenv("SA_KEY") == None:
    if not isfile("aksacarma-2e5f57e8e8c5.json"):
        if isfile("aksacarma_cloud_storage_sa_a850f4.zip"):
            with ZipFile("aksacarma_cloud_storage_sa_a850f4.zip", "r") as sa_key:
                sa_key.extractall(pwd=os.getenv("ZIP_PASS").encode())
    gcs_client = storage.Client.from_service_account_json("aksacarma-2e5f57e8e8c5.json")
else:
    gcs_client = storage.Client.from_service_account_info(
        literal_eval(os.getenv("SA_KEY"))
    )

app = FastAPI()
bucket = gcs_client.get_bucket(os.getenv("BUCKET_NAME", "aksa-carma-bucket-001"))


@app.on_event("startup")
async def startup():
    app.state.conn = await aiomysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        db=os.getenv("DB_NAME"),
        autocommit=True,
    )
    app.state.cur = await app.state.conn.cursor()


@app.on_event("shutdown")
async def shutdown():
    app.state.conn.close()


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")


@app.post(
    "/register",
    dependencies=[Depends(validate_credential)],
    response_model=RegisterResponse,
)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    avatar_url: str = Form(...),
):
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()

    await app.state.conn.ping()
    await app.state.cur.execute("SELECT * FROM user WHERE username = %s", (username,))
    result = await app.state.cur.fetchone()

    if result:
        return JSONResponse(
            {
                "error": True,
                "message": "Username already exists!",
            },
            status_code=409,
        )

    await app.state.cur.execute(
        "INSERT INTO user (username, pass_hash, name, avatar_url) VALUES (%s, %s, %s, %s)",
        (username, hashed_pass, name, avatar_url),
    )

    return JSONResponse({"error": False, "message": "User created!"}, status_code=200)


@app.post("/login", response_model=LoginResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()

    await app.state.conn.ping()
    await app.state.cur.execute(
        "SELECT * FROM user WHERE username = %s AND pass_hash = %s",
        (username, hashed_pass),
    )
    result = await app.state.cur.fetchone()

    if not result:
        return JSONResponse(
            {"error": True, "message": "Wrong username or password!"}, status_code=401
        )

    token = jwt.encode(
        {
            "user_id": result[0],
            "username": result[1],
            "name": result[3],
            "avatar_url": result[4],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(weeks=1),
        },
        os.getenv("SECRET_KEY"),
    )

    return JSONResponse(
        {
            "error": False,
            "message": "success",
            "login_result": {
                "user_id": result[0],
                "username": result[1],
                "name": result[3],
                "avatar_url": result[4],
                "token": token,
            },
        }
    )


@app.post("/get-disease-name", response_model=PredictionResponse)
async def get_disease_name(
    token: dict = Depends(validate_token), image: UploadFile = File(None)
):
    if not image:
        return JSONResponse(
            {"error": True, "message": "image parameter must not be empty"},
            status_code=422,
        )

    if not token:
        return JSONResponse(
            {"error": True, "message": "Invalid credentials!"}, status_code=401
        )

    prediction = detect_skin_image(await image.read())

    if not prediction:
        return JSONResponse(
            {
                "error": False,
                "message": "success",
                "prediction_result": {"prediction": None, "google_result": None},
            }
        )

    file_name = f"history/{token['user_id']}/{uuid.uuid4()}"
    blob = bucket.blob(file_name)
    blob.upload_from_file(image.file, rewind=True, content_type="image/png")
    image_url = blob.public_url

    google_results = await get_google_result(prediction)
    result = {"prediction": prediction, "google_result": google_results}

    await app.state.conn.ping()
    await app.state.cur.execute(
        "INSERT INTO history (user_id, prediction, image_url, datetime) VALUES (%s, %s, %s, %s)",
        (token["user_id"], prediction, image_url, datetime.datetime.now()),
    )

    history_id = app.state.cur.lastrowid

    await app.state.cur.executemany(
        "INSERT INTO search_result (history_id, title, url, description, image_url) VALUES (%s, %s, %s, %s, %s)",
        [
            (
                history_id,
                result["title"],
                result["url"],
                result["description"],
                result["image_url"],
            )
            for result in google_results
        ],
    )

    return JSONResponse(
        {"error": False, "message": "success", "prediction_result": result}
    )


@app.get("/get-user-history", response_model=List[HistoryResponse])
async def history(token: dict = Depends(validate_token)):
    await app.state.conn.ping()
    await app.state.cur.execute(
        "SELECT * FROM history WHERE user_id = %s ORDER BY datetime",
        (token["user_id"],),
    )
    histories_db = await app.state.cur.fetchall()

    if not histories_db:
        return []

    await app.state.cur.execute(
        "SELECT * FROM search_result WHERE history_id = %s", (histories_db[0][0],)
    )
    search_results_db = await app.state.cur.fetchall()

    histories = [
        {
            "prediction": prediction,
            "image_url": image_url,
            "datetime": str(datetime),
            "google_result": [
                {
                    "title": s_title,
                    "url": s_url,
                    "description": s_description,
                    "image_url": s_image_url,
                }
                for _, s_title, s_url, s_description, s_image_url in search_results_db
            ],
        }
        for _, _, prediction, image_url, datetime in histories_db
    ]

    return histories


@app.get("/get-user-data", response_model=UserResponse)
async def get_user_data(token: dict = Depends(validate_token)):
    if not token:
        return JSONResponse(
            {"error": True, "message": "Invalid credentials!", "user_data": None}, status_code=401
        )
    
    await app.state.conn.ping()
    await app.state.cur.execute(
        "SELECT id, username, name, avatar_url FROM user WHERE id = %s",
        (token["user_id"],),
    )

    user = await app.state.cur.fetchone()
    user_data = {
        "user_id": user[0],
        "username": user[1],
        "name": user[2],
        "avatar_url": user[3],
    }

    return JSONResponse({"error": False, "message": "success", "user_data": user_data})


@app.post("/update-user", response_model=UpdateResponse)
async def update_user(
    token: dict = Depends(validate_token),
    username: str = Form(None),
    password: str = Form(None),
    name: str = Form(None),
    avatar_image: UploadFile = File(None),
):
    if not token:
        return JSONResponse(
            {"error": True, "message": "Invalid credentials!"}, status_code=401
        )

    await app.state.conn.ping()
    if password:
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        await app.state.cur.execute(
            "UPDATE user SET pass_hash = %s WHERE id = %s",
            (hashed_pass, token["user_id"]),
        )

    if avatar_image:
        file_name = f"avatar/{token['user_id']}/{uuid.uuid4()}"
        blob = bucket.blob(file_name)
        blob.upload_from_file(avatar_image.file, rewind=True, content_type="image/png")
        avatar_url = blob.public_url
        await app.state.cur.execute(
            "UPDATE user SET avatar_url = %s WHERE id = %s",
            (avatar_url, token["user_id"]),
        )

    if username:
        await app.state.cur.execute(
            "UPDATE user SET username = %s WHERE id = %s", (username, token["user_id"])
        )

    if name:
        await app.state.cur.execute(
            "UPDATE user SET name = %s WHERE id = %s", (name, token["user_id"])
        )

    return JSONResponse({"error": False, "message": "success"})


if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=8005, log_level="info")
