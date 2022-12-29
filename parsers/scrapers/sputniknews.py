from datetime import datetime, timedelta
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parsers.models import NewsLinks
from parsers.scrapers.utils import save_last_date

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')


BASE_URL = "https://sputniknews-uz.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = session.get(link, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find('h1', class_='article__title')
    post_info['title'] = title.text
    # // ----  title  ----

    # ----  summary  ---- //
    summary = None
    try:
        _summary = soup.find('div', class_="article__announce-text")
        if _summary:
            summary = _summary.text
    except:
        pass
    post_info['summary'] = summary
    # // ----  summary  ----

    # ---- main image ---- //
    main_img = None
    main_img_div = soup.find("div", class_="media__size")
    if main_img_div:
        _main_image = main_img_div.find('img')
        if _main_image:
            try:
                main_img = encoder_utf_8(_main_image['src'])
            except:
                pass
    post_info['main_image'] = main_img
    # // ----  main image  ----

    # ---- main video ---- // TODO
    main_video = None
    main_video_div = soup.find("div", class_="media__size")
    if main_video_div:
        _main_video = main_img_div.find('iframe')
        if _main_video:
            try:
                main_video = encoder_utf_8(_main_video['src'])
            except:
                pass
    post_info['main_video'] = main_video
    # // ----  main video  ----

    body_div = soup.find("div", class_="article__body")

    # ---- texts & images ---- //
    _all_p = body_div.find_all("div", class_="article__block")
    image_items = soup.find_all("div", class_="article__photo-item")
    images = []
    text = ""
    if image_items:
        for image in image_items:
            img = image.find("img")
            if img:
                images.append(encoder_utf_8(img['src']))
    else:
        for p in _all_p:
            img = p.find('img')
            if img:
                try:
                    images.append(encoder_utf_8(img['src']))
                except:
                    pass
            text += p.text + '\n'
    post_info['text'] = text
    post_info['images'] = images

    # // ----  texts & images  ----

    # ----  video  ---- // TODO
    video_div = body_div.find("")
    print("video_div", video_div)
    video = None
    # if video_div:
    #     for _video in video_div:
    #         _iframe = _video.find("iframe")
    #         if _iframe:
    #             video = encoder_utf_8(_iframe['src'])
    # post_info['video'] = video
    # // ----  video  ----

    # ----  tags  ---- //
    _tags = soup.find_all('a', class_='tag__text')
    if _tags:
        tags = [
            {
                'name': tag.text,
                'url': BASE_URL + encoder_utf_8(tag['href'])
            }
            for tag in _tags
        ]
        post_info['tags'] = tags
    # // ----  tags  ----

    return post_info


# link = "https://sputniknews-uz.com/20221219/argentina-jahon-chempionatidagi-galabani-qanday-nishonladi---foto-30851869.html"
# link = "https://sputniknews-uz.com/20221219/prezident-sovgasining-birinchi-karvoni-hududlarga-jonatildi-30877409.html"
link = "https://sputniknews-uz.com/20221219/uqk-donetskdagi-kasalxonani-oqqa-tutdi--video-30870120.html"
# link = "https://sputniknews-uz.com/20221219/garb-endi-ukraina-qk-holati-haqidagi-haqiqatni-yashira-olmaydi--oav--30866897.html"
# link = "https://sputniknews-uz.com/20221220/shavkat-mirziyoev-30885939.html"
# link = "https://sputniknews-uz.com/20221212/bahodir-jalolov-bahrayn-vakilini-maglubiyatga-uchratdi--video--30663862.html"
# link = "https://sputniknews-uz.com/20221216/toshkentda-kurash-boyicha-musobaqalar-boshlandi---foto-30784835.html"
# link = "https://sputniknews-uz.com/20221219/jahon-chempionati-2022-eng-yaxshilar-aniqlandi-30845690.html"
# link = "https://sputniknews-uz.com/20221218/karate-wkf-ozbekistonlik-sportchilar-ochda-navbatdagi-oltin-medalni-qolga-kiritishdi---foto-30815121.html"
# link = "https://sputniknews-uz.com/20221216/bumerang-effekti-1-barrel-neft-100-dollarga-oshishi-bashorat-qilinmoqda-30793045.html"
# link = "https://sputniknews-uz.com/20221207/xavfni-korganda-darhol-harakat-qilish-kerak---moskvada-buxorolik-yigit-mukofotlandi--30546252.html"
# link = "https://sputniknews-uz.com/20221217/buxoroda-rossiya-davlat-neft-va-gaz-milliy-tadqiqot-universitetining-bolimi-ochildi---foto-30807207.html"
# result = get_post_detail(link=link)
# print(result)



def collect_new_links(last_date: datetime) -> List[str]:
    new_last_date = None
    has_next_page = True
    links = []
    months = {
        'Январ': '01',
        'Феврал': '02',
        'Март': '03',
        'Апрел': '04',
        'Май': '05',
        'Июн': '06',
        'Июь': '07',
        'Август': '08',
        'Сентябр': '09',
        'Октябр': '10',
        'Ноябр': '11',
        'Декабр': '12'
    }

    for i in range(1, 2700):
        req = requests.get(f'https://sputniknews-uz.com/archive/?page={i}')
        if not has_next_page:
            break
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            articles = soup.find_all('div', class_='list__item')
            for article in articles:
                link = article.find('a').get('href')
                try:
                    date = article.find('span', class_='date').text
                    date = date.split(' ')
                    if len(date) == 1:
                        time = date[0]
                        today = datetime.now()
                        date = today.strftime('%d-%m-%Y') + ' ' + time
                    elif len(date) == 2:
                        time = date[1]
                        today = datetime.now() - timedelta(days=1)
                        date = today.strftime('%d-%m-%Y') + ' ' + time
                    elif len(date) == 3:
                        day = date[0]
                        month = months[date[1].replace(',', '')]
                        year = datetime.now().strftime('%Y')
                        time = date[2]
                        date = day + '-' + month + '-' + year + ' ' + time
                        date = datetime.strptime(date, '%d-%m-%Y %H:%M')
                    else:
                        day = date[0]
                        month = months[date[1].replace(',', '')]
                        year = date[2][:-1]
                        time = date[3]
                        date = day + '-' + month + '-' + year + ' ' + time
                        date = datetime.strptime(date, '%d-%m-%Y %H:%M')     
                    date_in_datatime = datetime.strptime(date, '%d-%m-%Y %H:%M')
                    if date_in_datatime > last_date:
                        if link not in links:
                            links.append(link)
                        if not new_last_date:
                            new_last_date = date_in_datatime
                    else:
                        has_next_page = False
                        break
                except Exception as e:
                    logger.error(f'error in sputnik link collector: {e}')
    if new_last_date:
        save_last_date('sputniknews', new_last_date.timestamp()) 
    return links
