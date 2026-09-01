import pytest

from app.utils.rate_limit import SlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_repeat_of_same_request_is_one_unique():

    limiter = SlidingWindowRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    first = await limiter.check("1.1.1.1", "url-a")
    again = await limiter.check("1.1.1.1", "url-a")
    second = await limiter.check("1.1.1.1", "url-b")
    third = await limiter.check("1.1.1.1", "url-c")

    assert first[0] is True
    assert again[0] is True
    assert second[0] is True
    assert third[0] is False
    assert third[1] == 0
    assert third[2] >= 1


@pytest.mark.asyncio
async def test_clients_are_isolated():

    limiter = SlidingWindowRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    assert (await limiter.check("ip-a", "url"))[0]
    assert (await limiter.check("ip-b", "url"))[0]
    assert (
        await limiter.check("ip-a", "other")
    )[0] is False


def test_profile_post_body_still_parsed():

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/profile",
        json={
            "profile_url": (
                "https://www.linkedin.com/in/"
                "example-user"
            )
        },
    )

    assert response.status_code != 422
