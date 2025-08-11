# Use official Python slim image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . /app/

# Expose port
EXPOSE 10000

# Start Gunicorn server
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:10000"]
