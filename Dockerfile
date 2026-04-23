FROM python:3.11-slim

# Avoid .pyc, enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (Optional but recommended) install minimal OS deps if needed
# pyswisseph works without extra build deps if wheels are used.
# If you ever need to compile, uncomment:
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest (including sepl_18.se1)
COPY . .

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]