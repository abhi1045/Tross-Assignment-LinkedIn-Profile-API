from fastapi import APIRouter, HTTPException

from app.schemas.profile import (
    ProfileRequest,
    ProfileResponse,
)
from app.services.profile_service import (
    ProfileService,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["profiles"],
)

profile_service = ProfileService()


@router.post(
    "/profile",
    response_model=ProfileResponse,
)
async def get_profile(
    request: ProfileRequest,
):

    try:
        return await profile_service.get_profile(
            str(request.profile_url)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve profile information"
            ),
        )