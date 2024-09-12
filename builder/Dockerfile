# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.12

# Set environment variables
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

# Copy entrypoint script and make it executable
COPY builder/web_entrypoint.sh /builder/web_entrypoint.sh
RUN chmod +x /builder/web_entrypoint.sh

# Define environment variable
ENV NAME World

# Run web_entrypoint.sh when the container launches
ENTRYPOINT ["/builder/web_entrypoint.sh"]
