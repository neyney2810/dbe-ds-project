FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

COPY . .
CMD ["python", "server.py"]