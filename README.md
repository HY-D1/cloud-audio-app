# CS6620 – Audio-to-Text (English) with Timed Subtitles

## Overview
This project converts English audio into text with automatically timed subtitles.
It simulates AWS S3 + Lambda + Transcribe flow locally for development and will
later deploy to AWS EC2 or serverless services.


## How to Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py

docker build -t cloud-audio-app .
docker run --rm -p 8080:5000 -e PORT=5000 cloud-audio-app
# open http://127.0.0.1:8080
