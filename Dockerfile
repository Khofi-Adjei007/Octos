# Use the official Python image as a base
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install default-mysql-client for the mysqladmin tool
RUN apt-get update && apt-get install -y default-mysql-client

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js and npm (Tailwind's dependencies)
RUN apt-get update && apt-get install -y nodejs npm

# Install TailwindCSS, PostCSS, and Autoprefixer
RUN npm install -D tailwindcss postcss autoprefixer

# Initialize tailwind config
RUN npx tailwindcss init

# Copy the project files to the container
COPY . .

# Expose the Django default port
EXPOSE 8000

# Set the command to start the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Use the Python image as a base
FROM python:3.10-slim




