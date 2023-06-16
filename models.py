from typing import List, Optional

from pydantic import BaseModel


class LoginResult(BaseModel):
    user_id: int
    username: str
    name: str
    avatar_url: str
    token: str


class RegisterResponse(BaseModel):
    error: bool
    message: str


class LoginResponse(BaseModel):
    error: bool
    message: str
    login_result: Optional[LoginResult]


class SearchResult(BaseModel):
    title: str
    url: str
    description: str
    image_url: str


class PredictionResult(BaseModel):
    prediction: Optional[str]
    google_result: Optional[List[SearchResult]]


class PredictionResponse(BaseModel):
    error: bool
    message: str
    prediction_result: Optional[PredictionResult]


class HistoryResponse(BaseModel):
    prediction: str
    image_url: str
    datetime: str
    google_result: List[SearchResult]


class UpdateResponse(BaseModel):
    error: str
    message: str


class UserData(BaseModel):
    user_id: int
    username: str
    name: str
    avatar_url: str


class UserResponse(BaseModel):
    error: bool
    message: str
    user_data: Optional[UserData]
