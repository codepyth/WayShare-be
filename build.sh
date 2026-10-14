#!/usr/bin/env bash
# Render runs this on every deploy (Build Command: bash build.sh).
# Stop at the first failing command, so a broken deploy never goes live.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
