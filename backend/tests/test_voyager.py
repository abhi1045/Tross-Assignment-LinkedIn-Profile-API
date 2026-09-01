import pytest

from app.services.linkedin_voyager import (
    map_profile_view,
    skills_from_payload,
)
from app.utils.validators import (
    extract_profile_identifier,
    validate_linkedin_profile_url,
)


NESTED_PAYLOAD = {
    "profile": {
        "firstName": "Ada",
        "lastName": "Lovelace",
        "headline": "Mathematician",
        "summary": "Notes on the Analytical Engine.",
        "geoLocationName": "London, England",
        "miniProfile": {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "occupation": "Mathematician",
            "picture": {
                "com.linkedin.common.VectorImage": {
                    "rootUrl": (
                        "https://media.licdn.com/dms/image/v2/"
                    ),
                    "artifacts": [
                        {
                            "width": 100,
                            "fileIdentifyingUrlPathSegment": (
                                "small.jpg"
                            ),
                        },
                        {
                            "width": 800,
                            "fileIdentifyingUrlPathSegment": (
                                "large.jpg"
                            ),
                        },
                    ],
                }
            },
        },
    },
    "positionView": {
        "elements": [
            {
                "companyName": "Analytical Engines",
                "title": "Chief Programmer",
                "employmentType": "FULL_TIME",
                "locationName": "London",
                "description": "Wrote the first algorithm.",
                "timePeriod": {
                    "startDate": {
                        "year": 1842,
                        "month": 1,
                    }
                },
            }
        ]
    },
    "educationView": {
        "elements": [
            {
                "schoolName": "Home education",
                "degreeName": None,
                "fieldOfStudy": "Mathematics",
                "timePeriod": {
                    "startDate": {"year": 1828},
                    "endDate": {"year": 1835},
                },
            }
        ]
    },
    "skillView": {
        "elements": [
            {"name": "Mathematics"},
            {"name": "Programming"},
        ]
    },
    "certificationView": {
        "elements": [
            {
                "name": "Royal Society",
                "authority": "London",
                "timePeriod": {
                    "startDate": {
                        "year": 1830,
                        "month": 6,
                    }
                },
            }
        ]
    },
    "languageView": {
        "elements": [
            {
                "name": "English",
                "proficiency": "NATIVE_OR_BILINGUAL",
            }
        ]
    },
}


NORMALIZED_PAYLOAD = {
    "data": {
        "*profile": "urn:li:fs_profile:ada",
        "positionView": {
            "*elements": [
                "urn:li:fs_position:1",
            ]
        },
        "skillView": {
            "*elements": [
                "urn:li:fs_skill:1",
            ]
        },
    },
    "included": [
        {
            "entityUrn": "urn:li:fs_profile:ada",
            "firstName": "Grace",
            "lastName": "Hopper",
            "headline": "Rear Admiral",
            "summary": "COBOL",
            "locationName": "Arlington, Virginia",
            "miniProfile": {
                "occupation": "Computer scientist",
            },
        },
        {
            "entityUrn": "urn:li:fs_position:1",
            "companyName": "US Navy",
            "title": "Rear Admiral",
            "employmentType": "FULL_TIME",
            "timePeriod": {
                "startDate": {"year": 1944},
            },
        },
        {
            "entityUrn": "urn:li:fs_skill:1",
            "name": "COBOL",
        },
    ],
}


def test_validate_accepts_country_subdomain():

    url = "https://www.linkedin.com/in/example-user"
    assert (
        validate_linkedin_profile_url(url)
        == url
    )


def test_validate_rejects_non_https():

    with pytest.raises(ValueError):
        validate_linkedin_profile_url(
            "http://www.linkedin.com/in/example-user"
        )


def test_validate_rejects_non_linkedin_host():

    with pytest.raises(ValueError):
        validate_linkedin_profile_url(
            "https://example.com/in/example-user"
        )


def test_extract_rejects_path_injection():

    with pytest.raises(ValueError):
        extract_profile_identifier(
            "https://www.linkedin.com/in/../voyager"
        )


def test_extract_vanity():

    assert (
        extract_profile_identifier(
            "https://www.linkedin.com/in/example-user/"
        )
        == "example-user"
    )


def test_map_nested_profile_view():

    mapped = map_profile_view(
        NESTED_PAYLOAD,
        "https://www.linkedin.com/in/ada-lovelace",
    )

    assert mapped["name"] == "Ada Lovelace"
    assert mapped["headline"] == "Mathematician"
    assert mapped["location"] == "London, England"
    assert mapped["about"].startswith("Notes")
    assert mapped["profile_image"].endswith(
        "large.jpg"
    )
    assert mapped["experience"][0]["company"] == (
        "Analytical Engines"
    )
    assert mapped["experience"][0][
        "employment_type"
    ] == "Full-time"
    assert mapped["experience"][0]["start_date"] == (
        "1842-01"
    )
    assert mapped["education"][0]["start_year"] == 1828
    assert mapped["skills"] == [
        "Mathematics",
        "Programming",
    ]
    assert mapped["certifications"][0]["name"] == (
        "Royal Society"
    )
    assert mapped["languages"][0]["name"] == "English"


def test_map_normalized_profile_view():

    mapped = map_profile_view(
        NORMALIZED_PAYLOAD,
        "https://www.linkedin.com/in/ghopper",
    )

    assert mapped["name"] == "Grace Hopper"
    assert mapped["headline"] == "Rear Admiral"
    assert mapped["experience"][0]["company"] == (
        "US Navy"
    )
    assert mapped["skills"] == ["COBOL"]


def test_picture_rejects_non_licdn_host():

    payload = {
        "profile": {
            "firstName": "Test",
            "lastName": "User",
            "miniProfile": {
                "picture": {
                    "rootUrl": "https://evil.example/",
                    "artifacts": [
                        {
                            "width": 10,
                            "fileIdentifyingUrlPathSegment": (
                                "x.png"
                            ),
                        }
                    ],
                }
            },
        }
    }

    mapped = map_profile_view(
        payload,
        "https://www.linkedin.com/in/test-user",
    )

    assert mapped["profile_image"] is None


def test_skills_from_top_level_elements():

    payload = {
        "elements": [
            {"name": "Python"},
            {"skill": {"name": "FastAPI"}},
            {"name": "Python"},
        ]
    }

    assert skills_from_payload(payload) == [
        "Python",
        "FastAPI",
    ]
