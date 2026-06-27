# Self-contained: build from THIS folder.
#   docker build -t develop-analysis .
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8103

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8103"]
