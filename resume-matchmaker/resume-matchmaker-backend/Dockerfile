# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /Users/ansafnagori/Documents/Projects/resume-matchmaker/resume-matchmaker-backend

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_ENV production

# Run the app when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
