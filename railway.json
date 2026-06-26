FROM python:3.11-slim-bookworm

# Updating Packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    git curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copying Requirements
COPY requirements.txt /requirements.txt

# Installing Requirements
RUN pip3 install --upgrade pip
RUN pip3 install -U -r requirements.txt

# Setting up working directory
RUN mkdir /MusicPlayer
WORKDIR /MusicPlayer

# Copying project files
COPY . /MusicPlayer/

# Preparing for the Startup
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Running Music Player Bot
CMD ["/bin/bash", "/startup.sh"]
