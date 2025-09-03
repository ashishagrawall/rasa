FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Train the model during build (optional - can also be done at runtime)
RUN rasa train

# Expose ports
EXPOSE 5005 5055

# Default command
CMD ["rasa", "run", "--enable-api", "--cors", "*"]
