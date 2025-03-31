# Use the latest stable Python image with the specific version
FROM debian:latest

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies specified in the requirements.txt file
RUN apt-get update && \
    #apt-get install -y docker-ce-cli &&\
    pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8080

# Copy all the application files into the container
COPY main.py .

# Specify the command to run your application (e.g., Flask, Django, etc.)
# Example if you are using Flask:
# CMD ["python", "app.py"]

# Alternatively, if you have an entrypoint script, you could use:
ENTRYPOINT ["python", "main.py"]

# Set default command
CMD ["bash"]

