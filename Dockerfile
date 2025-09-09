FROM python:3.12-slim

# Avoid interactive tzdata prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Firefox + minimal tools for headless run
RUN apt-get update && apt-get install -y --no-install-recommends \
      firefox-esr \
      fonts-liberation \
      ca-certificates \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Install Python deps first (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add tests
COPY tests ./tests

# Default to running the tests
CMD ["pytest", "-q"]


# # Build
# docker build -t dinnova-qa:latest .

# # Run with your env vars
# docker run --rm \
#   -e DINNOVA_QA_LOGIN_URL="https://example.com/login" \
#   -e DINNOVA_QA_USERNAME="user@example.com" \
#   -e DINNOVA_QA_PASSWORD="supersecret" \
#   dinnova-qa:latest

# docker run --rm  --env-file .env dinnova-qa:latest
#x64
#docker buildx build --platform linux/amd64 -t dinnova-qa:latest .
#docker run --rm --platform linux/amd64 --env-file .env dinnova-qa:latest
