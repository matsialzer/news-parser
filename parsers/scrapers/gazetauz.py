from datetime import datetime
import re
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parsers.models import NewsLinks
from parsers.scrapers.utils import extract_dates, save_last_date
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')


encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

LAST_NEW_PAGE = 'https://www.gazeta.uz/uz/list/news/'
BASE_URL = "https://www.gazeta.uz"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = session.get(link, headers=headers)
        soup = BeautifulSoup(req.text, 'html.parser')

        _main_content = soup.find('div', class_='articlePage')
        # ----  title  ---- //
        title = _main_content.find('h1', id='article_title')
        post_info['title'] = title.text
        # // ----  title  ----

        # ----  main image & summary  ---- //
        main_image = None
        img_layout = _main_content.find('div', class_='articleTopBG')
        _summary = img_layout.find("h4")
        summary = ""
        if img_layout:
            _img = img_layout.find('img')
            if _img:
                try:
                    main_image = encoder_utf_8(_img['data-src'])
                except:
                    pass
        if _summary:
            summary = _summary.text

        post_info["summary"] = summary
        post_info['main_image'] = main_image
        # // ----  main image & summary  ----

        _body = _main_content.find('div', class_='articleContent')

        # ----  video  ---- //
        video = None  # TODO
        _all_p = _body.find_all("p")

        for p in _all_p:
            try:
                _iframe = p.find("iframe")
                if _iframe:
                    video = encoder_utf_8(_iframe['src'])
            except:
                pass

        post_info['video'] = video
        # // ----  video  ----

        # ----  texts  & images  ---- //
        text = ""
        images = []
        if _body:
            _images = _body.find_all("img", class_="fr-fic fr-dii lazy")
            for _img in _images:
                images.append(encoder_utf_8(_img["data-src"]))
            for p in _body:
                text += p.text + '\n'

        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & summary & images  ----

        # ----  tags  ---- //
        tags = []
        _tags_layout = soup.find('div', class_='articleTags')
        if _tags_layout:
            _tags = _tags_layout.find_all('a')
            if _tags:
                for tag in _tags:
                    tags.append({
                        'name': tag.text.strip(),
                        'url': encoder_utf_8(BASE_URL + tag["href"])
                    })
        post_info['tags'] = tags
        # // ----  tags  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


# test_link = 'https://www.gazeta.uz/oz/2022/12/17/mutolaa-sardor-salim/'
# test_link = "https://www.gazeta.uz/uz/2022/12/21/sell/"
# test_link = "https://www.gazeta.uz/oz/2022/12/20/wc-2022-moments/"
# test_link = "https://www.gazeta.uz/uz/2022/12/21/teenager/"
test_link = "https://www.gazeta.uz/uz/2022/12/19/wc-final/"
# res = get_post_detail(test_link)
# print(res)



def collect_new_links(last_date: datetime=None) -> List[str]:
    req = session.get(LAST_NEW_PAGE, headers=headers)
    links = []
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', class_='leftContainer')
        flag = True
        load_more = False
        new_last_date = None
        while flag:
            news_blocks = None
            if load_more:
                break
                load_more_link = _news_layout.find('a', class_='next')['href']
                req = session.get(encoder_utf_8(BASE_URL+load_more_link), headers=headers)
                if 200<= req.status_code < 300:
                    soup = BeautifulSoup(req.content, 'html.parser')
                    _news_layout = soup.find('div', class_='leftContainer')
                    news_blocks = _news_layout.find_all('div', class_='nblock')
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('div', class_='nblock')
            if not news_blocks:
                break
            for news_block in news_blocks:
                try:
                    a = news_block.find('a', class_='nimg')
                    url = encoder_utf_8(BASE_URL+a['href'])
                
                    _date: list = extract_dates(url)
                    time_block = news_block.find('div', class_='ndt')
                    date_str = time_block.text.strip()
                    time_regex = '([\d]{2}):([\d]{2})'
                    _res_time = re.search(time_regex, date_str).groups()
                    
                    if len(_res_time) == 2:
                        is_digits = all([i.isdigit() for i in _res_time])
                        if is_digits:
                            hour, minute = _res_time
                            _date.append(int(hour))
                            _date.append(int(minute))

                    date_time = datetime(*_date)
                    yield (url, date_time)
                    # if date_time > last_date:
                    #     if url not in links:
                    #         links.append(url)
                    #     if not new_last_date:
                    #         new_last_date = date_time
                    #     load_more = True
                    # else:
                    #     load_more = False
                    #     flag = False
                    #     break
                except Exception as e:
                    print(e)
                    logger.error(e)
            break
        if new_last_date:
            save_last_date('gazeta', new_last_date.timestamp())
    return links