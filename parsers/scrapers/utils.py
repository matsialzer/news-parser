import os, sys, django
import re
from typing import List

# ---------  Setup django  //  --------------
path_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(path_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
# ---------  //  Setup django  --------------

from django.conf import settings
from datetime import datetime


def save_last_date(site: str, timestamp: datetime.timestamp):
    path = f"{settings.BASE_DIR}/parsers/scrapers/data/{site}.txt"
    with open(path, 'w') as f:
        f.write(str(timestamp)) 


def extract_dates(url: str) -> List[int]:
    res = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', url)
    date_tuple = list(map(int, res.groups()))
    return date_tuple
