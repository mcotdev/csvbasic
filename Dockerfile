# Use the latest Alpine Linux image as the base
FROM alpine:latest

# Install Git, Python3, and pip3 without caching the index locally to keep the image small
RUN apk add --no-cache git python3 py-pip

# Clone the GitHub repository into the /app directory (ensure the repository URL is correct)
RUN git clone https://github.com/mcotdev/csvbasic.git /app

# Change the working directory inside the container to /app
WORKDIR /app

# Install Python dependencies listed in requirements.txt
RUN pip3 install -r requirements.txt

# Inform Docker that the container listens on the specified network ports at runtime
EXPOSE 5002

# Specify the command to run when the container starts
CMD ["python3", "csvbasic.py"]

