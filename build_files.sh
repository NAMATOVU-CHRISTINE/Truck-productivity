#!/bin/bash

# Build the project
echo "Building the project..."
python3 -m pip install -r requirements.txt

# Create staticfiles_build directory explicitly
mkdir -p staticfiles_build

# Collect static files
echo "Collect static..."
python3 manage.py collectstatic --noinput --clear

echo "Build End"
