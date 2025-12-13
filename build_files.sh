#!/bin/bash

# Build the project
echo "Building the project..."
python3 -m pip install -r requirements.txt

# Collect static files
echo "Collect static..."
python3 manage.py collectstatic --noinput --clear

echo "Build End"
