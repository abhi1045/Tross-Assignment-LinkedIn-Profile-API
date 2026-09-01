from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ProfileRequest(BaseModel):
    profile_url: HttpUrl = Field(
        description=(
            "Public LinkedIn profile URL in the "
            "form https://www.linkedin.com/in/<slug>"
        ),
        examples=[
            "https://www.linkedin.com/in/williamhgates"
        ],
    )


class Experience(BaseModel):
    company: str | None = None
    title: str | None = None
    employment_type: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class Education(BaseModel):
    school: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class Certification(BaseModel):
    name: str | None = None
    organization: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None
    credential_id: str | None = None


class Language(BaseModel):
    name: str
    proficiency: str | None = None


class ProfileMetadata(BaseModel):
    retrieved_at: datetime
    cached: bool = False
    status: str = "success"


class ProfileResponse(BaseModel):
    profile_url: str | None = None

    member_id: str | None = None
    name: str | None = None
    email: str | None = None
    headline: str | None = None
    location: str | None = None
    about: str | None = None

    profile_image: str | None = None
    background_image: str | None = None

    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[Certification] = Field(
        default_factory=list
    )
    languages: list[Language] = Field(default_factory=list)

    metadata: ProfileMetadata


class CacheListResponse(BaseModel):
    count: int
    profiles: list[ProfileResponse] = Field(
        default_factory=list
    )


class SessionStatusResponse(BaseModel):
    authenticated: bool
    oauth_configured: bool
    token_valid: bool = False
    name: str | None = None
