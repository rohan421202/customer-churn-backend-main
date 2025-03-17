import os
import shutil
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .. import schemas, database

router = APIRouter(
    tags=['File-Handling']
)

def get_folder_name(email):
    folder_name = ""
    for char in email:
        if char == '@':
            break
        folder_name += char
    return folder_name




