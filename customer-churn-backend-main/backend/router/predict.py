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

def correlation(dataset, threshold):
    col_corr = set()
    corr_matrix = dataset.corr()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            # considering abs value as in sklearn 
            if abs(corr_matrix.iloc[i, j]) > threshold:
                col_name = corr_matrix.columns[i]
                col_corr.add(col_name)
    
    return col_corr

@router.post('/testmodel')
def test_models(email: str, filename: str, modelname: str):
    path = os.getcwd()
    x = path.replace("\\", "/")
    folder_name = get_folder_name(email)
    file_location = f"{x}/{folder_name}/models/{modelname}"

    from joblib import load
    clf = load(file_location)

    df = pd.read_csv(f"{x}/{folder_name}/test/{filename}")
    org = pd.read_csv(f"{x}/{folder_name}/test/{filename}")
    for col in df.columns:
        if 'customer' in col or 'Customer' in col or 'ID' in col or 'id' in col or 'name' in col or 'Name' in col or 'RowNumber' in col:
            df.drop([col], axis = 1, inplace = True)

    na_variables = [ var for var in df.columns if df[var].isnull().mean() > 0 ]
    
    for col in na_variables:
        df[col] = df[col].fillna(df[col].mode()[0])


    if "churn" or "CHURN" in df.columns:
        df = df.rename({"churn" : "Churn"}, axis = 1)
    
    cat_variables = [ var for var in df.columns if len(df[var].unique()) < 10]
    
    if(df['Churn'][0] != 1 and df['Churn'][0] != 0):
        dictionary = {'yes': 1, 'no': 0, 'Yes': 1, 'No': 0}
        df['Churn'] = df['Churn'].map(dictionary)

    print(cat_variables)
 
    cat_variables.remove('Churn')
    for col in cat_variables:
        ordinal_labels = df.groupby([col])['Churn'].mean().sort_values().index
        ordinal_labels2 = {k:i for i,k in enumerate(ordinal_labels, 0)}
        df[f'{col}_ordinal_variables'] = df[col].map(ordinal_labels2)
        df.drop([col], axis = 1, inplace = True)

    for col in df.columns:
        if df[col].dtype == 'object':
            df.drop([col], axis = 1, inplace = True)

    X = df.drop(['Churn'], axis = 1)
    y = df['Churn']

    corr_features = correlation(X, 0.7)
    for col in corr_features:
        X.drop([col], axis = 1, inplace = True)

    X = df.drop('Churn', axis=1)
    res = clf.predict(X)
    k = 0
    dataframe = []
    for i in range(0, X.shape[0]):
        lst = []
        for j in X.columns:
            lst.append(X.iloc[i][j])
        lst.append(int(res[k]))
        k += 1
        dataframe.append(lst)
    
    cols = X.columns.tolist()
    cols.append('Churn')
    res = schemas.PredictedResult ( columns= cols, dataframe= dataframe )
    json_compatible_item_data = jsonable_encoder(res)
    return JSONResponse(content=json_compatible_item_data)


@router.post('/uploadtestfile')
def upload_test_file(email: str, file: UploadFile = File(...)):
    path = os.getcwd()
    x = path.replace("\\", "/")
    folder_name = get_folder_name(email)
    print(folder_name)
    file_location = f"{x}/{folder_name}/test/{file.filename}" 

    dictionary = { "email" : email }
    query = database.collection.find_one(dictionary, {"_id": 0})
    print(query)
    file_lst = query["test_files"]

    if file.filename in file_lst:
        return {"info" : "You already uploaded this file"}

    if file.filename not in file_lst:
        file_lst.append(file.filename)
        prev = {"email": email}
        nextt = {"$set": {"test_files" : file_lst}}
        database.collection.update_one(prev, nextt)

        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)    
    
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}    