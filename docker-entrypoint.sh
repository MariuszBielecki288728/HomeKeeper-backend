#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


# pwd && ls -al && source /venv/bin/activate
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
