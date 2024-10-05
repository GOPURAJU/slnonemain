# Use a Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        python3-dev \
        default-libmysqlclient-dev \
        pkg-config \
    && python -m pip install --upgrade pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose port (adjust as necessary)
EXPOSE 9000

# Run migrations and collect static files (adjust as necessary)
RUN python manage.py migrate
RUN python manage.py collectstatic --no-input

# Create superuser with specified username, email, and password
# Replace 'admin', 'admin@example.com', and 'adminpass' with your desired superuser details
RUN echo "from django.contrib.auth import get_user_model; \
User = get_user_model(); \
User.objects.create_superuser('raju1234', 'raju1234@example.com', 'adminpass')" | python manage.py shell

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:9000"]
