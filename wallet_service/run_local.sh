gunicorn --chdir ../ start_wallet_api:api --workers 2 --bind 0.0.0.0:5006 --reload