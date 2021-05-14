FROM python:3.9.1-buster

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /app 
EXPOSE 8000

RUN pip install poetry
COPY ./pyproject.toml /app/pyproject.toml
RUN poetry install
COPY . /app

CMD poetry run uvicorn app:app --reload --host 0.0.0.0 --log-level debug