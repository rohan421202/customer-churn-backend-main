import os
import shutil
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .. import schemas, database

router = APIRouter(
    tags=['User']
)