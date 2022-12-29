import json
from typing import List
from parsers.scrapers import (
    daryouz, aniquz, bugunuz, championatasia, gazetauz, 
    goal24uz, kunuz, olamsport, qalampiruz, sportsuz, 
    sputniknews, stadionuz, uzauz, zaminuz, bbc
)
from parsers.models import NewsLinks
from django.conf import settings
from datetime import datetime, date
from core.celery import app
from random import choice
import requests
import logging
import time
import os

logger = logging.getLogger('parsers')

API_URL = "http://api.news.e-konkurs.uz/api/v1/news"
API_URL = 'http://api.news.e-konkurs.uz/api/v1/home/news'
headers_api = {
    'api-key': 'VGhpcyBBcGktVG9rZW4gaGFzIGJlZW4gY3JlYXRlZCBieSBVbWlkIEt1cmJhbm92IGluIDI4LjEyLjIwMjI='
}

seconds = [0.5, 0.6, 0.7, 0.8, 0.9, 1]

def get_last_date(site: str) -> datetime:
    path = f"{settings.BASE_DIR}/parsers/scrapers/data/{site}.txt"
    try:
        file = open(path)
        timestamp = file.read()
        last_date = datetime.fromtimestamp(float(timestamp))
        return last_date
    except Exception as e:
        current_date = datetime.today()
        timestamp = current_date.timestamp()
        with open(path, 'w') as f:
            f.write(str(timestamp))
        return current_date


def get_last_date_and_link(site: str) -> List:
    path = f"{settings.BASE_DIR}/parsers/scrapers/data/{site}.txt"
    try:
        file = open(path)
        items = file.read().split(',')
        last_date = datetime.fromtimestamp(float(items[0]))
        last_link = items[1]
        return [last_date, last_link]
    except Exception as e:
        logger.critical('error in get last date and link')
        return False


def get_last_link(site: NewsLinks.Sites.choices) -> NewsLinks:
    daryo_news = NewsLinks.objects.filter(
            site=site
        ).order_by('-created_at')
    if daryo_news.exists():
        return daryo_news.first()


def send_post_info(post_info: dict) -> bool:
    try:
        image = None
        if post_info.get('main_image'):
            image = post_info['main_image']
        elif post_info.get('images'):
            image = post_info['images'][0]

        payload = {
            'title': post_info.get('title'),
            'img': image,
            'label': post_info.get('summary') or post_info.get('title'),
            'body': post_info['text'],
            'source': post_info['link'],
        }
        for ind, tag in enumerate(post_info.get('tags', [])):
            payload[f'tags[{ind}]'] = tag['name']

        # print(f'payload : {payload}')

        req = requests.request('POST', API_URL, headers=headers_api, data=payload)
        if 200 <= req.status_code < 300:
            return True
        else:
            logger.error(f'API status code : {req.status_code}, err_msg : {req.text}')
            return False
    except Exception as e:
        err = f'error sending post info : {e}'
        logger.error(err)
    return True


@app.task # 100% Completed
def daryo_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('daryo')
        new_links = daryouz.collect_new_links(last_date)
        for link in new_links:
            daryo_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = daryouz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def gazeta_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('gazeta')
        new_links = gazetauz.collect_new_links(last_date)
        for link in new_links:
            gazeta_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = gazetauz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def kun_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('kun')
        new_links = kunuz.collect_new_links(last_date)
        for link in new_links:
            kun_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = kunuz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def qalampir_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('qalampir')
        new_links = qalampiruz.collect_new_links(last_date)
        for link in new_links:
            qalampir_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))  
    elif link:
        try:
            post_info = qalampiruz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def uza_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('uza')
        new_links = uzauz.collect_new_links(last_date)
        for link in new_links:
            uza_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = uzauz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            print(f'error uza parser : {e}')
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def zamin_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('zamin')
        new_links = zaminuz.collect_new_links(last_date)
        for link in new_links:
            zamin_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = zaminuz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def sputniknews_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('sputniknews')
        new_links = sputniknews.collect_new_links(last_date)
        for link in new_links:
            sputniknews_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = sputniknews.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def aniq_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('aniq')
        new_links = aniquz.collect_new_links(last_date)

        for link in new_links:
            aniq_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = aniquz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def goal24_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date("goal24")
        new_links = goal24uz.collect_new_links(last_date)
        for link in new_links:
            goal24_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = goal24uz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def sports_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('sports')
        new_links = sportsuz.collect_new_links(last_date)
        for link in new_links:
            sports_parser.apply(
                kwargs={
                    'link': link
                    }
                )
            time.sleep(choice(seconds))
    elif link:
        try:
            post_info = sportsuz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def championat_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('championat')
        new_links = championatasia.collect_new_links(last_date)
        for link in new_links:
            championat_parser.apply(
                kwargs={
                    'link': link
                    }
                )
        time.sleep(choice(seconds))
    elif link:
        try:
            post_info = championatasia.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def olamsport_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('olamsport')
        new_links = olamsport.collect_new_links(last_date)
        for link in new_links:
            olamsport_parser.apply(
                kwargs={
                    'link': link
                    }
                )
        time.sleep(choice(seconds))
    elif link:
        try:
            post_info = olamsport.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed
def bugun_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('bugun')
        new_links = bugunuz.collect_new_links(last_date)
        for link in new_links:
            bugun_parser.apply(
                kwargs={
                    'link': link
                    }
                )
        time.sleep(choice(seconds))
    elif link:
        try:
            post_info = bugunuz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 50% HACK bu sayt ishlamayapti
def stadion_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_date = get_last_date('stadion')
        new_links = stadionuz.collect_new_links(last_date)
        print(f'new links : {len(new_links)}')
        print(f'new links : {new_links}')
        
        # for link in new_links:
        #     stadion_parser.apply(
        #         kwargs={
        #             'link': link
        #             }
        #         )
        # time.sleep(choice(seconds))
    elif link:
        try:
            post_info = stadionuz.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 90%
def bbc_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        last_info = get_last_date_and_link('bbc')
        if not last_info:
            return False
        new_links = bbc.collect_new_links(last_info)
        for link in new_links:
            bbc_parser.apply(
                kwargs={
                    'link': link
                    }
                )
        time.sleep(choice(seconds))
    elif link:
        try:
            post_info = bbc.get_post_detail(link)
            post_info['link'] = link
            send_post_info(post_info)
        except Exception as e:
            logger.error(e)
    else:
        return False
