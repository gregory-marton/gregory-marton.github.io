from bs4 import BeautifulSoup, SoupStrainer
import requests
from requests_file import FileAdapter
from requests_html import HTMLSession
import argparse

def init_argparse():
    parser = argparse.ArgumentParser(
        usage="python verify.py [OPTIONS] url",
        description="check html validity (loosely) and check links.")
    parser.add_argument("-x", "--expire", action="store", default=24, type=int,
                        help="Number of hours to refrain from checking external links.")
    parser.add_argument("url", action="store", help="The base url to mini-crawl and verify.")
    return parser

def verify_soup(soup):
    for link in soup.find_all('link'):
        print(f"Link: {link.get('href')}")
    for link in soup.find_all('a'):
        print(f"Url: {link.get('href')}")
        if link.get("img"):
            print(f"aImg: {link.get('img')}")
    for link in soup.find_all("img"):
        print(f"Img: {link.get('src')}")        

def verify(url):
    s = requests.Session()
    s.mount('file://', FileAdapter())
    page = s.get(url)
    assert page.status_code == 200
    verify_soup(BeautifulSoup(page.text))

    h = HTMLSession()
    h.mount("file://", FileAdapter())
    resp = h.get(url)
    resp.html.render() # populates resp.html.html
    verify_soup(BeautifulSoup(resp.html.html, "lxml"))

def main():
    parser = init_argparse()
    args = parser.parse_args()
    print(args.url, args.expire)
    verify(args.url.strip())

if __name__ == "__main__":
    main()
