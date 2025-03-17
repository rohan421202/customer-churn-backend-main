from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from .. import schemas, database
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter(
    tags=['Registration']
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup")
def register_user(request : schemas.User):

    hashed_pwd = pwd_context.hash(request.password)
    dictionary = {'user_id': request.user_id, 
                  'username': request.username,
                  'email': request.email,
                  'password': hashed_pwd,
                  'train_files': [],
                  'test_files': [],
                  'models': [],
                  'scores': [] 
                }

    check = {'email' : request.email}
    already_registered = database.collection.find_one(check, {'_id': 0})
    if already_registered:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="User already registered")

    database.collection.insert_one(dictionary)
    user = database.collection.find_one(check, {'_id': 0})
    return { "data": user}
    # newUser = schemas.User(user_id=request.user_id, username=request.username, email=request.email, password=request.password)
    # json_compatible_item_data = jsonable_encoder(newUser)
    # return JSONResponse(content=json_compatible_item_data)
    # return {"message" : "new user created successfully"}

@router.get("/users")
def get_all_users():
    all_users = list(database.collection.find({}, {'_id': 0}))
    # print(type(all_users)
    return {"data" : all_users}


@router.get("/user/{email}")
def get_specified_user(email: str):
    query = database.collection.find_one({'email': email}, {'_id': 0})
    return { "data" : query }

@router.put("/user/{email}")
def add_files(email: str):
    query = database.collection.find_one({'email': email}, {'_id': 0})
    # print(query)
    file_lst = query['files']

    # print(file_lst/, type(file_lst))
    file_lst.append("new_file")
    # print(file_lst)
    prev = {"email": email}
    nextt = {"$set": {"files": file_lst}}
    database.collection.update_one(prev, nextt)

    return { "data": "updated successfully"}