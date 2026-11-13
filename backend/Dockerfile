FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/models_cache
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends default-jdk-headless && rm -rf /var/lib/apt/lists/*
# torch CPU (beaucoup plus léger que la roue CUDA)
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
COPY requirements-base.txt requirements-ml.txt requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_NO_CACHE_DIR=0 pip install --default-timeout=300 --retries 10 -r requirements.txt
COPY . .
RUN useradd -m app && mkdir -p /models_cache && chown -R app /app /models_cache
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
