![Python](https://img.shields.io/badge/-Python-000000?style=for-the-badge&logo=Python)
![Docker](https://img.shields.io/badge/-Docker-000000?style=for-the-badge&logo=Docker)
![FastAPI](https://img.shields.io/badge/-FastAPI-000000?style=for-the-badge&logo=FastAPI)
![Black](https://img.shields.io/badge/-Black-000000?style=for-the-badge&logo=Black)

# FastAPI Celery SQLAlchemy Boilerplate

Warning: The program is still in development
A small boilerplate for backend projects on Python combining some usefull frameworks.

# How to run

## Docker

```
docker-compose up
```

## Tests

```
docker-compose -f docker-compose.test-cov.yml up -V --abort-on-container-exit --build
```

## Standalone

```
poetry run uvicorn app:app --reload
```
