# Set standard base image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Upgrade pip ensuring newest standard packaging protocols
RUN pip install --no-cache-dir --upgrade pip

# Create container requirements map purely and install 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source maps into the image natively 
COPY . .

# Safely expose standard fastAPI container port
EXPOSE 8000

# Fire off native command to startup ASGI web worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
