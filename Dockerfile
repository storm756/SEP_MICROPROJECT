# Step 1: Base image with Python 3.12
FROM python:3.12-slim

# Step 2: Set working directory inside container
WORKDIR /app

# Step 3: Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Copy application code
COPY . .

# Step 5: Expose application port
EXPOSE 8000

# Step 6: Run application using Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
