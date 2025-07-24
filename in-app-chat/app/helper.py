from starlette.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any

class StandardResponseModel(BaseModel):
    status_code: int  # HTTP Status Code
    message: str  # Description of the response
    data: Optional[Any] = None  # Any payload data

    def serialize(self):
        return self.model_dump()
    
    def dict(self):
        return self.model_dump()
    
    def __iter__(self):
        return iter(self.model_dump().items())


class ErrorResponseModel(BaseModel):
    status_code: int  # HTTP Status Code
    message: str  # Description of the response
    error: Optional[Any] = None  # Any payload data

    def serialize(self):
        return self.model_dump()
    
    def dict(self):
        return self.model_dump()
    
    def __iter__(self):
        return iter(self.model_dump().items())


def StandardResponse(status_code: int, message: str, data: Optional[Any] = None):
    return StandardResponseModel(status_code=status_code, message=message, data=data).serialize()


def StandardResponseWithoutSerialize(status_code: int, message: str, data: Optional[Any] = None):
    return StandardResponseModel(status_code=status_code, message=message, data=data)

def ErrorResponse(status_code: int, message: str, error: Optional[Any] = None):
    content = ErrorResponseModel(status_code=status_code, message=message, error=error).serialize()
    return JSONResponse(status_code=status_code, content=content)
