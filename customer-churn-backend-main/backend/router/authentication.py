from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from .. import schemas, database

router = APIRouter(
    tags=["Login"]
)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
def login(request : schemas.LoginUser):
    loginDict = { 'email': request.email }
    user = database.collection.find_one(loginDict, {'_id': 0})
    # print(type(user))
    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with details do not exist")

    # print(pwd_ctx.hash(request.password))
    # print(user['password'])
    check_pwd = pwd_ctx.verify(request.password, user['password'])
    
    if not check_pwd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")

    return { "data" : user }