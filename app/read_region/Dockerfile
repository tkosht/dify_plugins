FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
RUN apt-get update && apt-get install --no-install-recommends -y tesseract-ocr=5.3.0-2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock.txt
COPY models.lock.json ./
COPY scripts/fetch_models.py scripts/fetch_models.py
RUN python scripts/fetch_models.py /models && tesseract --version 2>&1 | head -1 | grep -Fx 'tesseract 5.3.0'
COPY service/ service/
COPY plugin/region_contract.py plugin/region_contract.py
RUN useradd --uid 10001 --create-home ocr && mkdir /state && chown ocr:ocr /state && dpkg-query -W > /app/os-packages.txt
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "service.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--log-level", "critical"]
