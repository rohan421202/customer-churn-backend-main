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

@router.post('/uploadtrainfile')
def upload_train_file(email: str, file: UploadFile = File(...)):
    path = os.getcwd()
    x = path.replace("\\", "/")
    folder_name = get_folder_name(email)
    print(folder_name)
    file_location = f"{x}/{folder_name}/train/{file.filename}" 

    dictionary = { "email" : email }
    query = database.collection.find_one(dictionary, {"_id": 0})
    print(query)
    file_lst = query["train_files"]

    # creating the directory for a particular user
    try:
        os.mkdir(f"{x}/{folder_name}")
        os.mkdir(f"{x}/{folder_name}/train")
        os.mkdir(f"{x}/{folder_name}/test")
        os.mkdir(f"{x}/{folder_name}/models")
    except FileExistsError:
        pass

    if file.filename in file_lst:
        return {"info" : "You already uploaded this file"}

    if file.filename not in file_lst:
        file_lst.append(file.filename)
        prev = {"email": email}
        nextt = {"$set": {"train_files" : file_lst}}
        database.collection.update_one(prev, nextt)

        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)    
    
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}


@router.post('/overview')
def get_overiew_data(email: str, filename : str):
    path = os.getcwd()
    x = path.replace("\\", "/")
    folder_name = get_folder_name(email)

    file_location = f"{x}/{folder_name}/train/{filename}"
    # file_location = file_location.replace("//", "/")
    df = pd.read_csv(file_location)
    for col in df.columns:
        if 'customer' in col or 'Customer' in col or 'ID' in col or 'id' in col or 'name' in col or 'Name' in col or 'RowNumber' in col:
            df.drop([col], axis = 1, inplace = True)

    if "churn" or "CHURN" in df.columns:
        df = df.rename({"churn" : "Churn"}, axis = 1)
    
    df = df.fillna('')
    num_rows = df.shape[0]
    num_features = df.shape[1]
    data_features = df.columns.tolist()
    na_variables = [ var for var in df.columns if df[var].isnull().mean() > 0 ]
    cat_variables = [ var for var in df.columns if len(df[var].unique()) < 10 and var != "Churn"]
    target_instance = df["Churn"].value_counts().to_frame()
    # print(target_instance)
    # print(target_instance["Churn"][0])
    # print(target_instance["Churn"][1])
    cat_data_lst = []
    for col in cat_variables:
        if col != "Churn":
            # print(df[col].value_counts().to_dict())
            cat_keys = df[col].value_counts().index.tolist()
            cat_vals = df[col].value_counts().tolist()
            # print(cat_keys)
            cat_data = [cat_keys, cat_vals]
            cat_data_lst.append(cat_data)

    numeric_col_names = [ var for var in df.columns if len(df[var].unique()) > 10 and df[var].dtypes != "object"]
    # print(numeric_col_names)

    numeric_data_lst = []
    for col in numeric_col_names:
        numeric_data_lst.append(df[col].tolist())

    item = schemas.DataOverview (
                rows= num_rows,
                cols= num_features,
                data_features=data_features,
                na_variables=na_variables,
                num_variables=numeric_col_names,
                cat_variables=cat_variables,
                target_instance=[ target_instance["Churn"][0], target_instance["Churn"][1] ],
                cat_col_data=cat_data_lst,
                numeric_col_data=numeric_data_lst
                )
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)