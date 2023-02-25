## Docker image build: docker build --tag cricbett-live-scheduler:1.0 --file scheduler-service/Dockerfile .
## This command is used to build a new Docker image with the tag cricbett-auth-svc:1.0 using the Dockerfile present in the auth_service directory.
## Run the command from parent directory (cricbett directory)
# docker tag cricbett-live-scheduler:1.0 qritwik/cricbett-live-scheduler:1.0
# docker push qritwik/cricbett-live-scheduler:1.0

##On EC2: ssh -i cricbett.pem ubuntu@13.233.78.222
## docker pull qritwik/cricbett-live-scheduler:1.0
## docker run -d -p 5009:5009 qritwik/cricbett-live-scheduler:1.0

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
WORKDIR /app/svc

# Create the /app/logs directory
RUN mkdir -p /app/logs

# Copy the requirements.txt file from the host to the container
COPY scheduler-service/requirements.txt /app/svc/

# Install the packages listed in requirements.txt
RUN pip3 install -r /app/svc/requirements.txt

# Copy the clients, cricbett_db, db, auth_service directories from the host to the container
COPY clients /app/svc/clients/
COPY cricbett_db /app/svc/cricbett_db/
COPY db /app/svc/db/
COPY scheduler-service /app/svc/scheduler-service/

# Expose port 5009 for the container
EXPOSE 5009

# Entrypoint for the container
ENTRYPOINT ["gunicorn"]

# Command to start the auth api using gunicorn with 2 worker processes, binding to all available network interfaces on port 5000
CMD ["--chdir", "scheduler-service/", "live_scheduler:api", "--workers", "2", "--bind", "0.0.0.0:5009"]
