from parsers.models import NewsLinks
from .utils import save_last_date
from datetime import datetime
from bs4 import BeautifulSoup
from urllib import parse
from typing import List
import requests
import logging
import re

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

LAST_NEWS_PAGE = 'https://daryo.uz/yangiliklar'
PAGINATION_URL = 'https://daryo.uz/yangiliklar?page={}'
BASE_URL = 'https://daryo.uz'


def get_post_detail(link: str) -> dict:
    post_info = {}
    try:
        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'html.parser')

        _main_content = soup.find('main', class_='maincontent')

        # ----  title  ---- //
        _article_info = _main_content.find('div', class_='inner__article-info border')
        title = _article_info.find('b')
        post_info['title'] = title.text
        # // ----  title  ----

        _default_section = soup.find('div', class_='default__section border')

        # ----  main image  ---- //
        main_image = None
        _figure = _default_section.find('figure')
        if _figure:
            _img = _figure.find('img')
            if _img:
                try:
                    main_image = encoder_utf_8(BASE_URL + _img['src'])
                except:
                    pass
        post_info['main_image'] = main_image
        # // ----  main image  ----

        # ----  video  ---- //
        _iframe = _default_section.find('iframe')
        video = None
        if _iframe:
            try:
                video = encoder_utf_8(_iframe['src'])
            except:
                pass
        post_info['video'] = video
        # // ----  video  ----

        # ----  texts & summary & images  ---- //
        _all_p = _default_section.find_all('p')
        text = ""
        summary = ""
        images = []
        if _all_p:
            for p in _all_p:
                img = p.find('img')
                if img:
                    img_url = encoder_utf_8(BASE_URL + img['src'])
                    if not main_image and video:
                        main_image = img_url
                        post_info['main_image'] = img_url
                        continue
                    images.append(img_url)
                # if not summary:
                #     summary = p.text
                #     continue
                text += p.text + '\n'
        post_info['summary'] = summary
        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & summary & images  ----

        # ----  category  ---- //
        category = None
        _category = _article_info.find('a', class_='category__title')
        if _category:
            category = {
                'name': _category.text.strip(),
                'url': encoder_utf_8(BASE_URL + _category['href'])
            }
        post_info['category'] = category
        # // ----  category  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


test_link = 'https://daryo.uz/2022/12/17/zoravonlik-haqida-ogiz-ochgan-odam-hukumatda-sazoyi-qilingan-barnogul-sanakulova-2016-yilgacha-zoravonlik-mavzusi-yopiq-bolgani-haqida-gapirdi'
# test_link = 'https://daryo.uz/2022/12/17/toshkentda-avtobuslarning-harakatlanish-oraliq-vaqti-25-30-daqiqadan-10-12-daqiqaga-qisqarmoqda'
# test_link = 'https://daryo.uz/2022/12/17/adminstratsiyada-yangi-tayinlovlar-amalga-oshirildi-qahramon-quronboyev-va-qahramon-sariyev-yangi-lavozimga-tayinlandi'
# test_link = 'https://daryo.uz/2022/12/16/rahmat-orniga-qurol-bilan-javob-berishdi-pokiston-senatori-tolibonning-chegaradagi-otishmasini-baholadi'
# test_link = 'https://daryo.uz/2022/12/17/toshkentda-molochnaya-kuxnya-korxonasi-davlat-kadastrlari-palatasi-aybi-bilan-15-mlrd-som-zarar-korgani-aytilmoqda'

# res = get_post_detail(test_link)
# print(res)

def extract_dates(url: str) -> List[int]:
    res = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', url)
    date_tuple = list(map(int, res.groups()))
    return date_tuple


def collect_new_links(last_date: datetime) -> List[str]:
    req = requests.get(LAST_NEWS_PAGE)
    links = []
    print(req.status_code)
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        main_content = soup.find('main', class_='maincontent')
        new_last_date = None
        page = 1
        if main_content:
            flag = True
            load_more = False
            while flag:
                mini_articles = None
                if load_more:
                    break
                    req = requests.get(PAGINATION_URL.format(page))
                    if 200<= req.status_code < 300:
                        soup = BeautifulSoup(req.content, 'html.parser')
                        main_content = soup.find('main', class_='maincontent')
                        if main_content:
                            mini_articles = main_content.find_all('div', class_='mini__article')
                            page += 1
                        else:
                            mini_articles = None
                    else:
                        load_more = False
                        flag = False
                        break
                else:
                    mini_articles = main_content.find_all('div', class_='mini__article')
                if not mini_articles:
                    break
                for article in mini_articles:
                    try:
                        category = article.find('a', class_='category__title')
                        if 'reklama' in category.text.lower():
                            continue

                        a = article.find('a', class_='mini__article-link')
                        url = encoder_utf_8(BASE_URL+a['href'])

                        _date: list = extract_dates(url)
                        time_block = article.find('time', class_='meta-date')
                        date_str = time_block.text.strip()
                        time_regex = '([\d]{2}):([\d]{2})' # extract time from date(18 avgust, 22:42)
                        _res_time = re.search(time_regex, date_str).groups()
                        
                        if len(_res_time) == 2:
                            is_digits = all([i.isdigit() for i in _res_time])
                            if is_digits:
                                hour, minute = _res_time
                                _date.append(int(hour))
                                _date.append(int(minute))

                        date_time = datetime(*_date)
                        if date_time > last_date:
                            if url not in links:
                                links.append(url)
                            if not new_last_date:
                                new_last_date = date_time
                            load_more = True
                        else:
                            load_more = False
                            flag = False
                            break
                    except Exception as e:
                        logger.error(e)
        if new_last_date:
            save_last_date('daryo', new_last_date.timestamp())

    return links

