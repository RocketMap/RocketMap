# Basic docker image for RocketMap
# Usage:
#   docker build -t rocketmap .
#   docker run -d -P rocketmap -a ptc -u YOURUSERNAME -p YOURPASSWORD -l "Seattle, WA" -st 10 --gmaps-key CHECKTHEWIKI

FROM python:2.7

# Default port the webserver runs on
EXPOSE 5000

# Working directory for the application
WORKDIR /usr/src/app

# Set Entrypoint with hard-coded options
ENTRYPOINT ["dumb-init", "-r", "15:2", "python", "./runserver.py", "--host", "0.0.0.0"]

# Set default options when container is run without any command line arguments
CMD ["-h"]

COPY requirements.txt /usr/src/app/

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && pip install --no-cache-dir dumb-init \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY package.json Gruntfile.js static01.zip /usr/src/app/
COPY static /usr/src/app/static

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl unzip \
 && curl -sL https://deb.nodesource.com/setup_6.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install \
 && npm run build \
 && rm -rf node_modules \
 && apt-get purge -y --auto-remove build-essential nodejs \
 && rm -rf /var/lib/apt/lists/*

# Copy everything to the working directory (Python files, templates, config) in one go.
COPY . /usr/src/app/
