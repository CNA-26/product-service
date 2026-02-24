from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

security = HTTPBearer()

def verify_admin(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
        token = credentials.credentials

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError:
               raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
              )
        except JWTClaimsError:
               raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims",
                    headers={"WWW-Authenticate": "Bearer"},
              )
        except JWTError:
              raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail= "Invalid token signature",
                    headers={"WWW-Authenticate": "Bearer"}
              )
        
        if payload.get("role") != "ADMIN":
              raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission"
              )
        
        return payload