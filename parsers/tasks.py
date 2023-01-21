from parsers.scrapers import (
    daryouz, aniquz, bugunuz, championatasia, gazetauz, 
    goal24uz, kunuz, olamsport, qalampiruz, sportsuz, 
    sputniknews, stadionuz, uzauz, zaminuz, bbc
)
from django.utils.timezone import make_aware
from parsers.models import NewsLinks
from django.conf import settings
from datetime import datetime, date
from core.celery import app
from random import choice
from typing import List
import requests
import logging
import json
import time
import os


logger = logging.getLogger('parsers')
logger.setLevel('INFO')

API_ENDPOINT = settings.API_ENDPOINT
API_KEY = settings.API_KEY

headers_api = {
    'api-key': API_KEY
}

seconds = [0.5, 0.6, 0.7, 0.8, 0.9]

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
    return False


def send_post_info(post_info: dict, post: NewsLinks) -> bool:
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

        post.payload=json.dumps(payload)
        post.save()
        if settings.SEND_TO_API:
            req = requests.request('POST', API_ENDPOINT, headers=headers_api, data=payload)
            if 200 <= req.status_code < 300:
                if post:
                    post.is_sent = True
                    post.save()
                return True
            else:
                api_error = f'API status code : {req.status_code}, err_msg : {req.text}'
                logger.error(api_error)
                post.err_msg = api_error
                post.save()
                return False
    except Exception as e:
        err = f'error sending post info : {e}'
        logger.error(err)
        post.err_msg = err
        post.save()
    return True


@app.task # 100% Completed (integrated into the database)
def daryo_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link, date_time in daryouz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'published_at': make_aware(date_time),
                    'site': NewsLinks.Sites.DARYO
                }
            )
            if not created:
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            daryo_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = daryouz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed (integrated into the database)
def gazeta_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link, date_time in gazetauz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'published_at': make_aware(date_time),
                    'site': NewsLinks.Sites.GAZETA
                }
            )
            if not created:
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            gazeta_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = gazetauz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed (integrated into the database)
def kun_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link, date_time in kunuz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'published_at': make_aware(date_time),
                    'site': NewsLinks.Sites.KUN
                }
            )
            if not created:
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            kun_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = kunuz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed (integrated into the database)
def qalampir_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link in qalampiruz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'site': NewsLinks.Sites.QALAMPIR
                }
            )
            if not created:
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            qalampir_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = qalampiruz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed (integrated into the database)
def uza_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link, date_time in uzauz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'published_at': make_aware(date_time),
                    'site': NewsLinks.Sites.UZA
                }
            )
            if not created: 
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            uza_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = uzauz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
        except Exception as e:
            logger.error(e)
    else:
        return False


@app.task # 100% Completed (integrated into the database)
def zamin_parser(beat: bool=False, link: str=None) -> None:
    if beat:
        link_objs = []
        for link, date_time in zaminuz.collect_new_links():
            new_post, created = NewsLinks.objects.get_or_create(
                url=link,
                defaults={
                    'published_at': make_aware(date_time),
                    'site': NewsLinks.Sites.ZAMIN
                }
            )
            if not created: 
                break
            link_objs.append(new_post)
        for link_obj in link_objs:
            zamin_parser.apply(
                kwargs={
                    'link': link_obj.url
                }
            )
            time.sleep(choice(seconds))
    elif link:
        try:
            post = NewsLinks.objects.get(url=link)
            post_info = zaminuz.get_post_detail(link)
            if post_info.get('errors'):
                post.err_msg=post_info['errors']
                post.save()
                return
            post.content=json.dumps(post_info)
            post.save()
            post_info['link'] = link
            send_post_info(post_info, post)
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
