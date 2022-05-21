FROM python:3.7-slim
WORKDIR /code
COPY . .
RUN apt-get update && apt-get upgrade -y && \
    pip install --upgrade pip && pip install -r requirements.txt
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000" ]
