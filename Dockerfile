# Gunakan base image Python
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy semua file ke container
COPY . /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Kumpulkan static files
RUN python manage.py collectstatic --noinput

# Jalankan aplikasi
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8999"]
