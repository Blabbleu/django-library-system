# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    default-mysql-client \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmariadb-dev-compat \
    pkg-config \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

COPY web_entrypoint.sh /web_entrypoint.sh
RUN chmod +x /web_entrypoint.sh
