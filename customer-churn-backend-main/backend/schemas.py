from pydantic import BaseModel
from typing import List

class User(BaseModel):
    user_id: int
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class Item(BaseModel):
    rows: int
    cols: int
    predt: List[int] = []
    predf: List[int] = []
    predL: List[int] = []
    tree_error: float
    forest_error: float
    logistic_reg_error: float


class DataOverview(BaseModel):
    rows: int
    cols: int
    data_features: List[str] = []
    na_variables: List[str] = []
    num_variables: List[str] = []
    cat_variables: List[str] = []
    target_instance: List[int] = []
    cat_col_data: List[List] = []
    numeric_col_data: List[List] = []

class TrainModel(BaseModel):
    models: List[dict] = {}

class PredictedResult(BaseModel):
    columns: List[str] = []
    dataframe: List[List] = []