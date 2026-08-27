from abc import ABC, abstractmethod
from typing import Any


class ProfileProvider(ABC):

    @abstractmethod
    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:
        """
        Retrieve profile data from a configured,
        authorized profile-data source.
        """
        raise NotImplementedError


class MockProfileProvider(ProfileProvider):

    async def get_profile(
        self,
        profile_url: str,
    ) -> dict[str, Any]:

        return {
            "profile_url": profile_url,
            "name": "Demo User",
            "headline": "Software Engineer",
            "location": "Bengaluru, Karnataka, India",
            "about": (
                "This is demo data returned by the "
                "development provider."
            ),
            "profile_image": None,
            "background_image": None,

            "experience": [
                {
                    "company": "Example Company",
                    "title": "Software Engineer",
                    "employment_type": "Full-time",
                    "location": "Bengaluru, India",
                    "start_date": "2023-01",
                    "end_date": None,
                    "description": "Building scalable applications.",
                }
            ],

            "education": [
                {
                    "school": "Example University",
                    "degree": "Bachelor of Engineering",
                    "field_of_study": "Computer Science",
                    "start_year": 2018,
                    "end_year": 2022,
                }
            ],

            "skills": [
                "Python",
                "FastAPI",
                "React",
            ],

            "certifications": [],

            "languages": [
                {
                    "name": "English",
                    "proficiency": "Professional",
                }
            ],
        }