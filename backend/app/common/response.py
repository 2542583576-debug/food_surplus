from pydantic import BaseModel
from typing import Any, Optional

class Result(BaseModel):
    code: int
    msg: str
    data: Optional[Any] = None

    @staticmethod
    def success(data: Any = None, msg: str = "success") -> Result:
        return Result(code=200, msg=msg, data=data)

    @staticmethod
    def fail(code: int = 400, msg: str = "fail", data: Any = None) -> Result:
        return Result(code=code, msg=msg, data=data)
