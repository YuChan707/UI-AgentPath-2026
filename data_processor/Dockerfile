# Self-contained: build from THIS folder (vendored dtos/ included).
#   docker build -t onlooker-data-processor .
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# The whole package (incl. the vendored dtos/) goes under /app/data_processor/.
COPY . /app/data_processor/

# /app makes `data_processor` importable for -m; the package dir makes the
# vendored `dtos` importable from within it.
ENV PYTHONPATH="/app:/app/data_processor"
ENV PYTHONUNBUFFERED=1
ENV LLM_TRANSPORT=auto

CMD ["python", "-m", "data_processor"]
