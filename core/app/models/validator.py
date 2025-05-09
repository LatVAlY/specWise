import uuid

from fastapi.encoders import jsonable_encoder


from starlette.responses import JSONResponse

from core.app.models.base_dto import BaseError, ErrorBaseResponse


def validate_uuid(uuid_string: str) -> uuid.UUID:
    try:
        return uuid.UUID(uuid_string)
    except ValueError:
        raise return_generic_http_error()

def return_not_found(message: str):
    return JSONResponse(status_code=404,
                        content=jsonable_encoder({
                            "detail": message
                        }))

def return_generic_http_error():
    return JSONResponse(status_code=400,
                        content=jsonable_encoder(
                            ErrorBaseResponse(
                                error=BaseError(code="T0001", message="Technical error occurred"),
                                success=False
                                ).to_json()
                            )
                        )

def task_already_exists_error():
    return JSONResponse(status_code=400,
                        content=jsonable_encoder(
                            ErrorBaseResponse(
                                error=BaseError(code="T0002", message="Task already exists"),
                                success=False
                                ).to_json()
                            )
                        )

def return_http_error(code:str, message:str):
    return JSONResponse(status_code=400,
                        content=jsonable_encoder(
                             ErrorBaseResponse(
                                error=BaseError(code=code, message=message),
                                success=False
                                ).to_json()
                            )
                        )
