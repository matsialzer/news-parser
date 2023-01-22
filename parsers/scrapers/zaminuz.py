from datetime import datetime, timedelta
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parsers.models import NewsLinks
from parsers.scrapers.utils import save_last_date
import logging


logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

LAST_NEWS_PAGE = 'https://zamin.uz/uz/lastnews/'
BASE_URL = "https://www.zamin.uz"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = session.get(link, headers=headers)
        soup = BeautifulSoup(req.text, 'html.parser')

        _article = soup.find('article', class_='article')

        # ----  title  ---- //
        # title = soup.find('div', class_='fheader').find("h1")
        try:
            title = _article.find_all('h1')
            post_info['title'] = title[0].text
        except Exception as e:
            logger.error(e)
        # // ----  title  ----
        main_div = soup.find("div", class_="fdesc")

        # ---- main image ---- //
        main_image = None

        if main_div:
            _main_image = main_div.find('img')
            # print(_main_image)
            if _main_image:
                try:
                    main_image = encoder_utf_8(BASE_URL+_main_image['src'])
                except Exception as e:
                    logger.error(f'{e} {_main_image}')
        post_info['main_image'] = main_image
        # // ---- main image ----

        # ----  video  ---- //
        video = None
        try:
            _figure = main_div.find('iframe')
            if _figure:
                try:
                    video = encoder_utf_8("https://"+_figure['data-src'])[6:]
                except Exception as e:
                    print(f'{e} {_figure}')
            post_info['video'] = video

            if not post_info.get('main_image'):
                yt_img_base_url = "https://img.youtube.com/vi/{}/maxresdefault.jpg"
                if post_info.get('video'):
                    if "youtube.com" in post_info['video']:
                        yt_video_id = post_info['video'].split('/')[-1]
                        yt_image = yt_img_base_url.format(yt_video_id)
                        post_info['main_image'] = yt_image
        except Exception as e:
            print(e)

        # // ----  video  ----

        # ----  texts & images  ---- //
        texts = main_div.text
        images = []
        if texts:
            post_info['text'] = texts
        try:
            images_ = main_div.find_all("img")[1:]
            for image in images_:
                try:
                    images.append(f"{BASE_URL}{encoder_utf_8(image['src'])}")
                except Exception as e:
                    # print(f'{e} {image}')
                    try:
                        images.append(f"{BASE_URL}{encoder_utf_8(image['data-src'])}")
                    except Exception as e:
                        print(f'{e} {image}')
            post_info['images'] = images
        except Exception as e:
            print(e)
        # // ----  texts & images  ----

        # ---- tags ---- //
        # try:
        #     tag_div = soup.find_all("div", class_="fcat")[-1].find("a")
        #     tags = {
        #         'name': tag_div.text,
        #         'url': "https:" + encoder_utf_8(tag_div['href'])
        #     }
        #     post_info['tags'] = tags
        # except Exception as e:
        #     print(e)
        # // ----  tags  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


# link = "https://zamin.uz/uz/dunyo/110109-janubiy-sudan-prezidenti-ommaviy-tadbirda-ishtonini-hollab-qoydi-video.html"
# link = "https://zamin.uz/uz/dunyo/110191-marhum-turmush-ortogining-ovozini-eshitish-uchun-har-kuni-metroga-boradigan-ayol.html"
# link = "https://zamin.uz/uz/sport/110228-jch2022-goliblari-qaysi-chempionatlarda-top-suradi.html"
# link = "https://zamin.uz/uz/jamiyat/110104-nemis-sharhlovchisining-etirofi-biz-mundialga-hamjinsbozlikni-qollagani-keldik.html"
link = "https://zamin.uz/uz/dunyo/110230-argentinaliklar-jahon-chempionatidagi-galabani-qanday-nishonladi-foto.html"
# res = get_post_detail(link=link)
# print(res)


def collect_new_links(last_date: datetime=None) -> List[str]:
    new_last_date = None
    has_next_page = True
    links = []
    for i in range(1, 5):
        if not has_next_page:
            break
        if i == 1:
            url = LAST_NEWS_PAGE
        else:
            url = f'https://zamin.uz/uz/lastnews/page/{i}/'
        req = requests.get(url)
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            articles = soup.find_all('div', class_='short-item')
            for article in articles:
                date = article.find('div', class_='short-date').text
                link = article.find('a').get('href')[2:]
                if 'tps' in link:
                    link = link.replace('tps', 'https')
                else:
                    link = 'https://' + link
                if 'Bugun' in date or 'Kecha' in date:
                    time = date.split(',')[1]
                    if 'Bugun' in date:
                        date = datetime.now().strftime('%d-%m-%Y')
                    else:
                        date = (datetime.now() - timedelta(days=1)).strftime('%d-%m-%Y')
                    date = date + ' ' + time
                else:
                    day = date.split(',')[0]
                    time = date.split(',')[1]
                    date = day + ' ' + time
                date_in_datatime = datetime.strptime(date, '%d-%m-%Y %H:%M')
                yield(link, date_in_datatime)
                # if date_in_datatime > last_date:
                #     links.append(link)
                #     if not new_last_date:
                #         new_last_date = date_in_datatime
                # else:
                #     has_next_page = False
                #     break
    if new_last_date:
        save_last_date('zamin', new_last_date.timestamp())
    return links
