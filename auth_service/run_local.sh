gunicorn --chdir ../ start_auth_api:api --workers 2 --bind 0.0.0.0:5007 --reload