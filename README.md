# Tross-Assignment-LinkedIn-Profile-API

# LinkedIn Profile API

## Overview

LinkedIn Profile API is a lightweight web application that accepts a LinkedIn profile URL and returns available profile information as structured JSON.

The project consists of:

* A Python 3.12 backend
* FastAPI for the REST API
* React for the frontend
* Bun for frontend dependency management and builds
* `uv` for Python dependency management
* Docker for consistent deployment
* A lightweight caching layer
* A provider abstraction for profile data retrieval

The application is designed as a proof-of-concept and hiring challenge submission with a focus on:

* Clean API design
* Low infrastructure requirements
* Structured JSON responses
* Separation of concerns
* Secure configuration management
* Easy deployment
* Future scalability

The challenge requires a publicly deployed HTTPS API that accepts a LinkedIn profile URL and returns structured information available from the profile, including details such as name, headline, location, experience, education, skills, certifications, languages, and profile images when available.

---

# Features

## Current Features

* Accepts a LinkedIn profile URL
* Validates the submitted URL
* Exposes a REST API
* Returns structured JSON
* Supports profile fields such as:

  * Name
  * Headline
  * Location
  * About
  * Profile image
  * Background image
  * Experience
  * Education
  * Skills
  * Certifications
  * Languages
* Provides automatic OpenAPI documentation through FastAPI
* Includes a React frontend
* Includes lightweight in-memory caching
* Uses asynchronous Python APIs
* Supports Docker deployment
* Keeps secrets outside the source repository through environment variables
* Includes health-check support

---

# Technology Stack

| Layer                    | Technology                      |
| ------------------------ | ------------------------------- |
| Backend Language         | Python 3.12                     |
| Backend Framework        | FastAPI                         |
| ASGI Server              | Uvicorn                         |
| Python Package Manager   | uv                              |
| Frontend                 | React                           |
| Frontend Build Tool      | Vite                            |
| Frontend Package Manager | Bun                             |
| HTTP Client              | HTTPX                           |
| Data Validation          | Pydantic                        |
| Containerization         | Docker                          |
| Orchestration            | Docker Compose                  |
| Cache                    | Lightweight in-memory TTL cache |

---

# Architecture

```text
                         User
                           │
                           ▼
                    ┌──────────────┐
                    │ React UI     │
                    │ Static Build │
                    └──────┬───────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ FastAPI Backend  │
                  │ Python 3.12      │
                  └────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │ Validation Layer  │
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │ Profile Service   │
                 └─────────┬─────────┘
                           │
                   ┌───────▼────────┐
                   │ TTL Cache      │
                   └───────┬────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Profile Provider  │
                 └─────────┬─────────┘
                           │
                           ▼
                 LinkedIn / Authorized
                 Data Access Method
```

The application uses a provider abstraction to separate:

1. API logic
2. Validation
3. Data retrieval
4. Response normalization
5. Caching

This makes it easier to change the underlying data-access implementation without changing the public API.

---

# Project Structure

```text
linkedin-profile-api/
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── profile.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── profile_service.py
│       │   └── provider.py
│       │
│       └── utils/
│           ├── __init__.py
│           └── cache.py
│
└── frontend/
    ├── package.json
    ├── bun.lock
    ├── vite.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        └── index.css
```

---

# API Documentation

## Health Check

### Request

```http
GET /health
```

### Response

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

# Get Profile Information

## Endpoint

```http
POST /api/v1/profile
```

## Request Headers

```http
Content-Type: application/json
```

## Request Body

```json
{
  "profile_url": "https://www.linkedin.com/in/example-profile/"
}
```

## Successful Response

```json
{
  "profile_url": "https://www.linkedin.com/in/example-profile/",
  "name": "Example User",
  "headline": "Software Engineer",
  "location": "Bengaluru, Karnataka, India",
  "about": "Example profile description.",
  "profile_image": "https://example.com/profile-image.jpg",
  "background_image": null,

  "experience": [
    {
      "company": "Example Company",
      "title": "Software Engineer",
      "employment_type": "Full-time",
      "location": "Bengaluru, India",
      "start_date": "2023-01",
      "end_date": null,
      "description": "Example job description."
    }
  ],

  "education": [
    {
      "school": "Example University",
      "degree": "Bachelor of Engineering",
      "field_of_study": "Computer Science",
      "start_year": 2018,
      "end_year": 2022
    }
  ],

  "skills": [
    "Python",
    "FastAPI",
    "React"
  ],

  "certifications": [],

  "languages": [
    {
      "name": "English",
      "proficiency": "Professional"
    }
  ],

  "metadata": {
    "retrieved_at": "2026-08-27T10:00:00Z",
    "cached": false,
    "status": "success"
  }
}
```

---

# Error Responses

## Invalid URL

```json
{
  "detail": "Please provide a valid LinkedIn profile URL"
}
```

## Profile Not Available

```json
{
  "detail": "Profile information is unavailable"
}
```

## Temporary Service Failure

```json
{
  "detail": "Profile service temporarily unavailable"
}
```

## Internal Server Error

```json
{
  "detail": "Unable to retrieve profile information"
}
```

---

# Authentication and Credentials

The backend may require credentials for the configured data-access method.

For development or authorized access, credentials must be supplied through environment variables.

Example:

```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

## Important Security Rules

The following must never be committed to Git:

* LinkedIn email address
* LinkedIn password
* Session cookies
* Authentication tokens
* API keys
* Authorization headers
* Browser storage
* Environment files containing real credentials

The `.env` file must remain excluded from version control.

Example:

```gitignore
.env
.env.*
!.env.example
```

The repository should contain only:

```text
.env.example
```

The `.env.example` file must contain placeholder values only.

Example:

```env
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
```

## Production Secret Management

For production deployments, credentials should be injected through the hosting platform's secret-management system rather than stored in the Docker image.

Recommended:

```text
Deployment Platform
        │
        │ Secure Environment Variables
        ▼
Docker Container
        │
        ├── LINKEDIN_EMAIL
        └── LINKEDIN_PASSWORD
```

Never do this:

```dockerfile
ENV LINKEDIN_EMAIL=my-real-email@example.com
ENV LINKEDIN_PASSWORD=my-real-password
```

Also never place credentials directly in:

* Source code
* Git commits
* Dockerfiles
* Docker images
* README files
* Frontend environment variables
* Browser JavaScript

Credentials must remain backend-only.

---

# Local Development

## Requirements

Install:

* Python 3.12
* uv
* Bun
* Docker (optional)

---

# Backend Setup

Move into the backend directory:

```bash
cd backend
```

Install dependencies:

```bash
uv sync
```

Create your environment file:

```bash
cp ../.env.example ../.env
```

Run the backend:

```bash
uv run uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# Frontend Setup

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
bun install
```

Start the development server:

```bash
bun run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# Docker Deployment

The application uses a multi-stage Docker build.

## Build Stages

### Stage 1 — Frontend

Bun is used to:

* Install frontend dependencies
* Build the React application

The result is static files.

### Stage 2 — Backend Dependencies

`uv` is used to:

* Resolve Python dependencies
* Create the production virtual environment

### Stage 3 — Production

The final production image contains:

* Python 3.12
* Python dependencies
* FastAPI
* Uvicorn
* Application code
* Built React static files

It does not need to run:

* Bun
* Node.js
* Vite
* npm
* A React development server

---

# Build Docker Image

From the project root:

```bash
docker compose build
```

---

# Run Docker Container

```bash
docker compose up
```

Run in detached mode:

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs -f
```

Stop the application:

```bash
docker compose down
```

---

# Environment Variables

Example `.env` configuration:

```env
APP_NAME=LinkedIn Profile API
APP_VERSION=1.0.0

CACHE_TTL_SECONDS=300
REQUEST_TIMEOUT_SECONDS=15

ALLOWED_ORIGINS=http://localhost:5173

LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=

PROVIDER_BASE_URL=
PROVIDER_API_KEY=
```

The exact provider configuration depends on the chosen data-access implementation.

---

# Resource Requirements

## Target Deployment

This project is initially designed to run on a small instance with:

```text
RAM: 512 MB
CPU: 0.1 vCPU
```

This is suitable for:

* Demonstrations
* Hiring challenges
* Low traffic
* Development testing
* Small numbers of requests

## Runtime Optimizations

The application is designed to remain lightweight:

* One application process
* Asynchronous I/O
* Static frontend files
* No React development server
* No Bun runtime in production
* Small in-memory cache
* Limited dependency set
* HTTP connection timeouts
* Single Uvicorn worker

Recommended runtime configuration:

```text
Workers: 1
Memory Limit: 512 MB
CPU Limit: 0.1 vCPU
Cache Size: Small
Request Timeout: 10–30 seconds
```

---

# What Is In Scope

The following functionality is within the current project scope.

## Backend API

* Public REST API
* HTTPS deployment through the hosting platform or reverse proxy
* Profile URL validation
* Structured JSON responses
* FastAPI OpenAPI documentation
* Health check endpoint
* Error handling

## Profile Data Structure

The API is designed to support:

* Name
* Headline
* Location
* About section
* Profile image
* Background image
* Work experience
* Education
* Skills
* Certifications
* Languages

The actual availability of fields depends on what is available to the configured data-access method.

## Frontend

* React user interface
* Profile URL input
* API request submission
* Loading state
* Error display
* Structured profile display

## Infrastructure

* Docker deployment
* Multi-stage builds
* Python 3.12
* uv
* Bun
* React
* FastAPI

## Security

* Environment-based configuration
* No credentials in source code
* No secrets in Git
* Backend-only secret handling

---

# What Is Out of Scope

The following are intentionally outside the initial MVP scope.

## High-Scale Infrastructure

Not included initially:

* Kubernetes
* Multi-region deployments
* Multi-node clusters
* Auto-scaling infrastructure
* Redis clusters
* Distributed caching
* Message queues
* Microservices architecture

These add complexity and are unnecessary for an initial hiring-challenge implementation.

---

## High-Concurrency Processing

The initial deployment is not intended for:

* Hundreds of simultaneous requests
* Thousands of requests per second
* Large distributed workloads

The initial infrastructure target is optimized for a demonstration and low traffic.

---

## Persistent Database

The MVP does not require a database.

Reasons:

* The primary operation is request → retrieve → normalize → return.
* Persistent profile storage introduces additional privacy, retention, and security considerations.
* A database can be introduced later if caching, historical results, or user accounts are required.

---

## User Authentication

The frontend does not currently include:

* User registration
* Login
* Password management
* User accounts
* OAuth for application users

The LinkedIn credentials, if used for the backend's configured access mechanism, are infrastructure credentials and are not frontend user credentials.

---

## Browser Automation Infrastructure

The MVP architecture is not designed around:

* Persistent Chromium instances
* Selenium grids
* Large Playwright worker pools
* Multiple browser processes

A full browser-based architecture can require substantially more CPU and memory than the target 512 MB / 0.1 vCPU deployment.

---

# Scaling Strategy

The MVP is intentionally simple. If traffic increases, the application can be scaled in stages.

---

## Stage 1 — Current MVP

```text
1 Docker Container

├── FastAPI
├── Uvicorn
├── In-memory cache
└── Static React files
```

Suitable for:

* Demo usage
* Low traffic
* Hiring challenge review

Target:

```text
512 MB RAM
0.1 vCPU
1 Worker
```

---

## Stage 2 — Moderate Traffic

Upgrade resources:

```text
1–2 GB RAM
1 vCPU
```

Add:

* Persistent cache
* Rate limiting
* Structured logging
* Metrics
* Improved connection pooling

Architecture:

```text
Load Balancer
      │
      ▼
FastAPI
      │
      ├── Cache
      │
      └── Profile Provider
```

---

## Stage 3 — Production Scale

Use:

```text
Load Balancer
      │
      ▼
Multiple API Instances
      │
      ├── Redis Cache
      ├── Database
      ├── Queue
      └── Background Workers
```

Potential improvements:

* Horizontal scaling
* Redis
* PostgreSQL
* Background job processing
* Request queues
* Centralized logs
* Monitoring
* Metrics
* Alerting

---

# Scaling Considerations

## 1. Move From In-Memory Cache

Current:

```text
Application Instance
      │
      ▼
In-Memory TTL Cache
```

Problem:

Each application instance has its own cache.

At scale:

```text
Multiple API Instances
        │
        ▼
    Shared Redis Cache
```

Benefits:

* Shared cache
* Lower provider requests
* Faster repeated responses
* Reduced backend load

---

## 2. Add Rate Limiting

Rate limiting is recommended to protect:

* The backend
* Infrastructure resources
* External data providers

Possible limits:

```text
10 requests/minute per IP
100 requests/hour per IP
```

The exact values should be configured according to expected usage and the limits of the authorized integration.

---

## 3. Add Request Queuing

For expensive profile retrieval operations:

```text
User Request
     │
     ▼
API
     │
     ▼
Queue
     │
     ▼
Worker
     │
     ▼
Result Storage
```

This prevents expensive operations from blocking all API requests.

---

## 4. Add Horizontal Scaling

When CPU usage increases:

```text
                Load Balancer
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       API #1       API #2       API #3
```

This requires shared infrastructure for:

* Cache
* Rate limits
* Job queues
* Persistent data

---

# Performance Considerations

## Current Optimizations

The project uses:

* Async HTTP operations
* Lightweight dependencies
* Single application worker
* Small TTL cache
* Static frontend deployment
* Multi-stage Docker builds
* No production Node.js process
* No production Bun process

## Future Optimizations

Potential improvements:

* HTTP connection pooling
* Shared Redis cache
* Background jobs
* Response compression
* CDN for frontend assets
* Database indexing
* Metrics-driven autoscaling

---

# Security Considerations

## Credentials

Credentials must:

* Stay in environment variables
* Never be returned by the API
* Never be sent to the React frontend
* Never be logged
* Never be committed to Git

## Logging

Sensitive information should be redacted.

Do not log:

```text
Passwords
Authorization headers
Cookies
Session tokens
API keys
```

Prefer logging:

```text
Request ID
Timestamp
Response status
Processing duration
Error category
```

---

# Caching

The initial implementation uses an in-memory TTL cache.

Example:

```text
Request
   │
   ▼
Cache Hit?
 ┌───────┐
 │ Yes   │────► Return Cached Response
 └───────┘

 │ No
 ▼

Retrieve Data
      │
      ▼
Normalize Response
      │
      ▼
Store in Cache
      │
      ▼
Return Response
```

The cache should be treated as an optimization rather than permanent storage.

---

# Known Limitations

The following limitations should be documented clearly.

## Profile Data Availability

The API can only return fields available through the configured data-access method.

Therefore:

* Some fields may be missing
* Some profiles may contain incomplete information
* Some information may not be available
* Profile visibility can affect results

The API should gracefully return `null` or empty arrays for unavailable fields.

---

## Resource Limits

The target infrastructure:

```text
512 MB RAM
0.1 vCPU
```

is intentionally minimal.

This configuration is suitable for low traffic but is not designed for large-scale concurrent workloads.

---

## Single Instance Cache

The initial cache:

* Is memory-based
* Is not shared between instances
* Is cleared when the container restarts

A shared cache should be introduced when scaling horizontally.

---

## External Dependency

Profile retrieval depends on the availability and behavior of the configured authorized data-access mechanism.

Failures can occur due to:

* Network errors
* Authentication issues
* Provider changes
* Timeouts
* Access restrictions

The API should handle these errors without exposing sensitive implementation details.

---

# Monitoring and Observability

For production, consider adding:

* Health checks
* Structured logs
* Request IDs
* Response timing
* Error-rate monitoring
* Memory monitoring
* CPU monitoring

Example metrics:

```text
requests_total
requests_failed
request_duration_seconds
provider_requests_total
cache_hits_total
cache_misses_total
```

---

# Testing

Recommended test layers:

## Unit Tests

Test:

* URL validation
* Response normalization
* Cache behavior
* Error handling

## API Tests

Test:

```text
POST /api/v1/profile
GET /health
Invalid requests
Provider failures
```

## Integration Tests

Test:

```text
Frontend
    │
    ▼
API
    │
    ▼
Configured Provider
```

---

# Future Improvements

Potential future improvements include:

* Shared distributed cache
* PostgreSQL for optional persistent storage
* Background workers
* Request queues
* Rate limiting
* Monitoring and metrics
* Centralized logging
* Improved retry strategies
* Circuit breakers
* Horizontal scaling
* CDN deployment for the frontend
* More detailed API filtering options
* Webhook or asynchronous job APIs

---

# API Design Principles

The API follows these principles:

1. Validate input early.
2. Keep the public API independent from the data provider.
3. Normalize responses into a stable schema.
4. Do not expose credentials.
5. Handle unavailable fields gracefully.
6. Return structured error responses.
7. Keep infrastructure simple for the MVP.
8. Scale infrastructure only when required.

---

# Deployment Checklist

Before deployment:

* [ ] Confirm Python version is 3.12
* [ ] Confirm `uv.lock` is committed
* [ ] Confirm `bun.lock` is committed
* [ ] Confirm `.env` is not committed
* [ ] Confirm credentials are stored as deployment secrets
* [ ] Confirm API documentation works
* [ ] Confirm `/health` works
* [ ] Confirm invalid URLs are rejected
* [ ] Confirm frontend can reach the API
* [ ] Confirm Docker image builds successfully
* [ ] Confirm secrets are not present in Docker image layers
* [ ] Confirm logs do not expose credentials
* [ ] Confirm production HTTPS is configured
* [ ] Document known limitations

---

# Development Status

```text
Backend API:              Implemented
React Frontend:           Implemented
Docker Deployment:        Implemented
uv Integration:           Implemented
Bun Integration:          Implemented
Health Endpoint:          Implemented
Response Schema:          Implemented
Caching:                  Implemented
Provider Abstraction:     Implemented
Authorized Data Provider: To Be Configured
Rate Limiting:            Planned
Distributed Cache:        Planned
Horizontal Scaling:       Future
Monitoring:               Future
```

---

# License

This project is created as a technical and hiring challenge implementation.

Before deploying or using the project beyond the challenge, review the applicable terms, permissions, privacy requirements, and rules governing the chosen profile-data access method.
