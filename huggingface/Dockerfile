# Hugging Face Space Configuration
# This runs both the Express server and the Telegram bot

FROM python:3.11-slim

WORKDIR /app

# Install Node.js for the server
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json for Node dependencies
COPY package.json .
RUN npm install --production

# Copy all application files
COPY . .

# Create data directory for bot cache
RUN mkdir -p /data/bot2

# Expose port for the server
EXPOSE 7860

# Start script
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
