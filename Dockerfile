# Use the official Python image as the base image
FROM --platform=linux/amd64 python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
Run pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the NiceGUI application into the container
COPY . .

# Expose port 8080
EXPOSE 8080

# Start the NiceGUI application
CMD ["python", "gui/main.py"]
