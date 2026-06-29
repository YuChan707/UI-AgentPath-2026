<<<<<<< HEAD
# Self-contained: build from THIS folder (no shared sibling needed).
#   docker build -t embeding-service .
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
=======
# Build from the repo root (needs the shared dtos/ package):
#   docker build -f embeding_service/Dockerfile -t embeding-service .
FROM python:3.11-slim
WORKDIR /app

COPY embeding_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dtos/ ./dtos/
COPY embeding_service/ ./embeding_service/

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
EXPOSE 8100

CMD ["uvicorn", "embeding_service.main:app", "--host", "0.0.0.0", "--port", "8100"]
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
