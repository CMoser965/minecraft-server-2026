# Use a lightweight Python image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install requests library (no need for requirements.txt for one lib)
RUN pip install requests python-dotenv mcrcon mcstatus

# Copy the script
COPY server_status.py .

# Run unbuffered (so logs show up in Docker immediately)
CMD ["python", "-u", "server_status.py"]