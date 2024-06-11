FROM alpine:latest

# Install Git and Python
RUN apk add --no-cache git python3 py-pip

# Clone the GitHub repository
RUN git clone https://github.com/your-username/your-repo-name.git /app

# Set working directory to /app
WORKDIR /app

# Install dependencies
RUN pip3 install -r requirements.txt

# Expose port 5002
EXPOSE 5002

# Run command when container starts
CMD ["python3", "mytest.py"]
