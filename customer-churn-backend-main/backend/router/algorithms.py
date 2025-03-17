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

@router.post('/trainmodel')
def train_models(email: str, filename: str):
    path = os.getcwd()
    x = path.replace("\\", "/")
    folder_name = get_folder_name(email)
    file_location = f"{x}/{folder_name}/train/{filename}"


    dictionary = {"email": email}
    query = database.collection.find_one(dictionary, {"_id": 0})
    models_trained_already = query["models"]
    model_name = f"{filename[:-4]}.joblib" 

    if model_name in models_trained_already:
        print("model already trained")
        return {"info" : "model trained already"}

    df = pd.read_csv(file_location)

    if "churn" or "CHURN" in df.columns:
        df = df.rename({"churn" : "Churn"}, axis = 1)
        
    for col in df.columns:
        if 'customer' in col or 'Customer' in col or 'ID' in col or 'id' in col or 'name' in col or 'Name' in col or 'RowNumber' in col:
            df.drop([col], axis = 1, inplace = True)

    na_variables = [ var for var in df.columns if df[var].isnull().mean() > 0 ]
    # print('null value containing column',na_variables)
    
    for col in na_variables:
        df[col] = df[col].fillna(df[col].mode()[0])

    cat_variables = [ var for var in df.columns if len(df[var].unique()) < 10]


    if(df['Churn'][0] != 1 and df['Churn'][0] != 0):
        dictionary = {'yes': 1, 'no': 0, 'Yes': 1, 'No': 0}
        df['Churn'] = df['Churn'].map(dictionary)

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


    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    # from xgboost import XGBClassifier
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import GridSearchCV
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

    model_params = {
        'Decision Tree' : {
            'model' : DecisionTreeClassifier(),
            'params' : {
                'random_state' : [1, 5, 10, 50, 100]
            }
        },
        'Random Forest' : {
            'model' : RandomForestClassifier(),
            'params' : {
                'n_estimators' : [1, 5, 10, 50, 100]
            }
        },
        'Logistic Regression' : {
            'model' : LogisticRegression(solver='liblinear', multi_class='auto'),
            'params' : {
                'C' : [1, 5, 10, 50, 100]
            }
        },
        'Gradient Boosting': {
            'model': GradientBoostingClassifier(),
            'params': {
                'n_estimators': [1, 5, 10, 50, 100]
            }
        },
        # 'xg_boost': {
        #     'model': XGBClassifier(),
        #     'params': {
        #         'n_estimators': [1, 5, 10, 50, 100, 500, 1000],
        #         'learning_rate': [0.01, 0.05, 0.1]
        #     }
        # }
    }

    scores = []

    test_model = ""
    max_score = 0
    i = 0
    for model_name, mp in model_params.items():
        clf = GridSearchCV(mp['model'], mp['params'], cv = 5, return_train_score=False)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        
        if max_score < accuracy_score(y_test, y_pred):
            test_model = model_name
            max_score = accuracy_score(y_test, y_pred)

        i += 1
        scores.append({
            'model' : model_name,
            'best_score' : clf.best_score_,
            'best_params' : clf.best_params_,
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred, average='weighted')
        })

    # print(test_model)
    score_df = pd.DataFrame(scores, columns=['model', 'best_score', 'best_params', 'accuracy', 'precision', 'recall', 'f1-score'])
    # print(score_df)

    best_model = model_params[test_model]
    # print(best_model)

    # print(f"{x}/{folder_name}/models/{filename[:-4]}.joblib")
    best_clf = GridSearchCV(best_model['model'], best_model['params'], cv = 5, return_train_score=True)
    best_clf.fit(X, y)
    
    from joblib import dump
    dump(best_clf, f"{x}/{folder_name}/models/{filename[:-4]}.joblib")

    dictionary = { "email" : email }
    query = database.collection.find_one(dictionary, {"_id": 0})
    models = query["models"]
    score_lst = query["scores"]

    if f"{filename[:-4]}.joblib" not in models:
        models.append(f"{filename[:-4]}.joblib")
        prev = {"email": email}
        nextt = {"$set": {"models" : models}}
        database.collection.update_one(prev, nextt)

        score_lst.append(scores)
        prev = {"email": email}
        nextt = {"$set": {"scores": score_lst}}
        database.collection.update_one(prev, nextt)

    model = schemas.TrainModel(models= scores)
    json_compatible_item_data = jsonable_encoder(model)
    return JSONResponse(content=json_compatible_item_data)