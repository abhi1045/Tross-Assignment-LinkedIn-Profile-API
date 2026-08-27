from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

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
        return (
            await profile_service.get_profile(
                str(request.profile_url)
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Profile service "
                "temporarily unavailable"
            ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to retrieve "
                "profile information"
            ),
        ) from error
