## Docker image build: docker build --tag cricbett-feeds-svc:1.0 --file feeds_service/Dockerfile .
## This command is used to build a new Docker image with the tag cricbett-auth-svc:1.0 using the Dockerfile present in the auth_service directory.
## Run the command from parent directory (cricbett directory)
#
## Docker run: docker run -d -p 5001:5001 cricbett-feeds-svc:1.0
## This command is used to run the newly built Docker image in detached mode, mapping port 5000 of the host to port 5000 of the container.

FROM python:3.10-alpine

RUN apk add --update --no-cache \
    build-base \
    libffi-dev \
    gcc \
    mariadb-connector-c-dev \
    python3-dev \
    musl-dev \
    wget \
    nano \
    curl

# Set the working directory to /app/api
WORKDIR /app/api

# Create the /app/logs directory
RUN mkdir -p /app/logs

# Copy the requirements.txt file from the host to the container
COPY feeds_service/requirements.txt /app/api/

# Upgrade pip to latest version
RUN  pip3 install --upgrade pip

# Install the packages listed in requirements.txt
RUN pip3 install -r /app/api/requirements.txt

# Copy the clients, cricbett_db, db, auth_service, feeds_service directories from the host to the container
COPY clients /app/api/clients/
COPY cricbett_db /app/api/cricbett_db/
COPY db /app/api/db/
COPY auth_service /app/api/auth_service/
COPY feeds_service /app/api/feeds_service/

# Expose port 5001 for the container
EXPOSE 5001

# Entrypoint for the container
ENTRYPOINT ["gunicorn"]

# Command to start the auth api using gunicorn with 2 worker processes, binding to all available network interfaces on port 5000
CMD ["--chdir", "feeds_service/", "start_feeds_api:api", "--workers", "2", "--bind", "0.0.0.0:5001"]
