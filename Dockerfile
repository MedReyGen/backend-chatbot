# Base image menggunakan Python 3.10
FROM python:3.10-slim

# Set working directory di dalam container
WORKDIR /app

# Copy requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tambahkan gunicorn untuk server produksi
RUN pip install gunicorn

# Copy seluruh kode aplikasi ke container
COPY . .

# Set environment variable untuk Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Port yang akan digunakan oleh aplikasi
ENV PORT=8080

# Command untuk menjalankan aplikasi
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app