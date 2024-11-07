# Use the official Python image as a base
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files to the container
COPY . .

# Expose the Django default port
EXPOSE 8000

# Set the command to start the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
