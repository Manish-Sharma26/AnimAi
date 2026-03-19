FROM manimcommunity/manim:stable
USER root
RUN apt-get update && apt-get install -y ffmpeg sox && rm -rf /var/lib/apt/lists/*
RUN /opt/venv/bin/pip install --no-cache-dir "setuptools<81" manim-voiceover gTTS