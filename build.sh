#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Gom file tĩnh (CSS/JS)
python manage.py collectstatic --no-input

# Chạy migrate database
python manage.py migrate