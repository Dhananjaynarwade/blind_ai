#!/bin/bash
echo "Installing required packages..."
pip install -r requirements.txt

echo "Setting HTTPS environment variable..."
export USE_HTTPS=True

echo "Starting Flask application with HTTPS..."
python app.py 