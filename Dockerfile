# Use the latest stable Python image with the specific version
FROM debian:latest

# Set the working directory inside the container
WORKDIR /app

SHELL ["/bin/bash", "-c"]

# Copy the requirements file into the container
COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y python3 python3-pip python3-venv
RUN apt-get install -y ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce-cli
RUN python3 -m venv .venv
RUN source .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Copy the application file into the container
COPY main.py .

# Alternatively, if you have an entrypoint script, you could use:
ENTRYPOINT [".venv/bin/python", "main.py"]