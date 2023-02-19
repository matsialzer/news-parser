from parsers.scrapers.utils import save_last_date
from requests.adapters import HTTPAdapter, Retry
from parsers.models import NewsLinks
from datetime import datetime, date
from bs4 import BeautifulSoup
from urllib import parse
from typing import List
import requests
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

LAST_NEWS_PAGE = 'https://www.bbc.com/uzbek/topics/c8y949r98pgt'
PAGINATION_URL = '?page={}'
# BASE_URL = "https://bbc.com/uzbek"
BASE_URL = "https://www.bbc.com/uzbek/topics/c8y949r98pgt"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = session.get(link, headers=headers)
        soup = BeautifulSoup(req.text, 'html.parser')

        # ----  title  ---- //
        title = soup.find('h1', id="content")
        post_info['title'] = title.text
        # // ----  title  ----

        # ---- main image ---- //
        main_img = None
        main_image_div = soup.find("div", class_="bbc-997y1y")
        if main_image_div:
            _main_image = main_image_div.find("img")
            if _main_image:
                try:
                    main_img = encoder_utf_8(_main_image['src'])
                except:
                    pass
        post_info['main_image'] = main_img

        # // ---- main image ----
        main_div = soup.find("main", role="main")

        # ---- summary ---- //
        summary = ""
        summary_div = soup.find("div", class_="bbc-3edg7g")
        if summary_div:
            summary_p = summary_div.find_all("p")
            if summary_p:
                for p in summary_p:
                    summary += p.text + "\n"
        # print(f'summary : {summary}')
        post_info["summary"] = summary

        # // ---- summary ----

        # ---- links ---- //
        _all_links = main_div.find_all("a", class_="bbc-n8oauk")
        if _all_links:
            links = [
                {
                    'name': _link.text,
                    'url': BASE_URL + encoder_utf_8(_link['href'])
                }
                for _link in _all_links
            ]
            post_info["links"] = links

        # ---- images and texts ---- //
        images = []
        text = ""
        _all_p = main_div.find_all("p", class_="bbc-1y32vyc e17g058b0")
        _all_images_div = main_div.find_all("img", class_="e3vrtyk0")
        if _all_p:
            for p in _all_p:
                # if not post_info.get('summary'):
                #     post_info['summary'] = p.text
                text += p.text + "\n"
        post_info["text"] = text

        if _all_images_div:
            for _image in _all_images_div[1:]:
                if _image:
                    images.append(encoder_utf_8(_image['src']))
        post_info["images"] = images

        # ---- tags ---- //
        _tags = soup.find_all("li", class_="bbc-qbu3pw")

        if _tags:
            tags = [
                {
                    'name': _tag.find("a").text,
                    'url': BASE_URL + encoder_utf_8(_tag.find("a")['href'])
                }
                for _tag in _tags
            ]
            post_info['tags'] = tags

        # // ----  tags  ----

        # ---- video ---- //
        video = None
        video_div = soup.find("div", class_="bbc-1kvmfu4")
        # print("video", video_div)
        if video_div:
            video = video_div["data-e2e"]
        post_info["video"] = video
        # // ---- video ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


# link = "https://www.bbc.com/uzbek/world-64056269"
# link = "https://www.bbc.com/uzbek/uzbekistan-64024872"
link = "https://www.bbc.com/uzbek/world-64063132"


# link = "https://www.bbc.com/uzbek/world-49934733"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_info: List = None) -> List[str]:
    # last_date, last_link = last_info
    # last_date: date = last_date.date()
    new_last_date = None
    new_last_link = None
    load_more = False
    link_find = False
    page_link = BASE_URL
    flag = False
    links = []
    # check_link = requests.get(last_link)
    # print(f'last link status : {check_link.status_code}')
    # if check_link.status_code != 200:
    #     logger.critical(f'link not found : {last_link}')
    #     return links
    req = requests.get(BASE_URL)
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        main_content = soup.find('ul', attrs={'data-testid': 'topic-promos'})
        if main_content:
            news_blocks = main_content.find_all('li', class_='bbc-t44f9r')  # class_="bbc-v8cf3q" changed
            print("news_blocks", news_blocks)
            if news_blocks:
                flag = True
    while flag:
        if load_more:
            try:
                # print('load more')
                next_page = soup.find('span', visibility='ALL')
                next_url = next_page.find('a')['href']
                # print(f'next url : {next_url}')
                req = requests.get(next_url)
                if 200 <= req.status_code < 300:
                    main_content = soup.find('ul', attrs={'data-testid': 'topic-promos'})
                    news_blocks = main_content.find_all('li', class_='bbc-v8cf3q')
                    page_link = next_url
            except Exception as e:
                # print(f'error in load more : {e}')
                break
        for news_block in news_blocks:
            try:
                link = news_block.find('a')['href']
                date_block = news_block.find('time')['datetime']
                dtime = datetime.strptime(date_block.strip(), '%Y-%m-%d')
                yield (link, dtime)
                # if dtime.date() > last_date:
                #     if link not in links:
                #         links.append(link)
                #     if not new_last_date:
                #         new_last_date = dtime
                #     if not new_last_link:
                #         new_last_link = link
                #     load_more = True
                # elif dtime.date() == last_date:
                #     if link == last_link:
                #         link_find = True
                #         load_more = False
                #         flag = False
                #         break
                #     else:
                #         if link not in links:
                #             links.append(link)
                #         if not new_last_date:
                #             new_last_date = dtime
                #         if not new_last_link:
                #             new_last_link = link
                #         load_more = True
                # else:
                #     load_more = False
                #     flag = False
                #     break
            except Exception as e:
                # print(f'error bbc collector : {e}')
                logger.error(f'error in bbc collector : {e}')
                load_more = False
                flag = False
                break
        break
    # if new_last_date:
    #     if link_find:
    #         data = f"{new_last_date.timestamp()},{new_last_link}"
    #         save_last_date('bbc', data)
    #     else:
    #         logger.critical(f'bbc last link not found : {last_link}, page link : {page_link}')
    return links
