# News Parsers

## Create new virtual environment
```bash
python3 -m venv env
```

## Activate virtual environment
```bash
source env/bin/activate
```

## Install packages
```
pip3 install -r requirements.txt
```

## Initialization commands to start a django project
```bash
python3 manage.py makemigrations
python3 manage.py migrate
yes | python3 manage.py collectstatic
```

## Run django project
```bash
python3 manage.py runserver
```

## Run celery beat
```bash
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Run celery worker
```bash
celery -A core worker -c 20 -l info
```