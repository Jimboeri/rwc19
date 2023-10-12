FROM python:3.11.6-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir code
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get update && apt-get -y install libpq-dev gcc
RUN pip install -r requirements.txt
copy . /code/
WORKDIR /code/swim

