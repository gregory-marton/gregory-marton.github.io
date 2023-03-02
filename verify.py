from bs4 import BeautifulSoup, SoupStrainer
from lxml import etree
from requests_file import FileAdapter
from requests_html import HTMLSession
import argparse
import io
import json
import logging
import re
import requests
import sys
import time
import urllib

DEFAULT_EXPIRY_SECONDS=24*60*60
RETURNS403 = ["researchgate.net", "350.org", "hrw.org", "camfed.org", "givedirectly.org", "amnh.org",
              "wildernessawareness.org", "neaq.org"]
logging.getLogger().setLevel(logging.INFO)

def init_argparse():
    parser = argparse.ArgumentParser(
        usage="python verify.py [OPTIONS] url",
        description="check html validity (loosely) and check links.")
    parser.add_argument("-x", "--expire hours", action="store", default=DEFAULT_EXPIRY_SECONDS,
                        type=int, dest="expire",
                        help="Number of hours to refrain from checking external links.")
    parser.add_argument("-m", "--markfile filename", action="store", default=".verify-marks.json", type=str,
                        dest="markfile",
                        help="Path to a file containing last successful check times for external sites.")
    parser.add_argument("url", action="store", help="The base url to mini-crawl and verify.")
    return parser

class Verifier():
    def __init__(self, markfile=None, expiration=DEFAULT_EXPIRY_SECONDS):
        self.markfile = markfile
        self.expiration = expiration
        self.marks = {}
        if markfile:
            try:
                with open(markfile, "r") as infile:
                    self.marks = json.load(infile)
            except FileNotFoundError:
                pass
        self.now = time.time()

    def verify_link(self, context_url, url):
        if re.search(r'://', url):
            last_checked = 0
            if url in self.marks:
                last_checked = self.marks[url]
            logging.info(f'foreign: {url} expires {last_checked + self.expiration - self.now} w/{self.expiration}')
            if last_checked + self.expiration > self.now:
                logging.info(f'recently ok {url}')
            else:
                logging.info(f'foreign: {url}')
                page = self.plain_session.get(url)
                if re.search(r'\b(linkedin\.com)\b', url):
                    assert page.status_code == 999, url  # Denied because they want you to use their api
                elif re.search(f'\\b({"|".join(map(re.escape,RETURNS403))})\\b', url):
                    assert page.status_code == 403, url  # Forbidden because they don't like bots.
                else:
                    assert page.status_code == 200, (url, page.status_code)
                self.marks[url] = self.now
                if self.markfile:
                    with open(self.markfile, "w") as outfile:
                        json.dump(self.marks, outfile)
        elif re.search(r'\.html?$', url):
            absolute_url = urllib.parse.urljoin(context_url, url)
            self.verify(absolute_url)
        elif re.search(r'^mailto:', url):
            assert re.fullmatch(r'mailto:\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', url), url
        else:
            absolute_url = urllib.parse.urljoin(context_url, url)
            logging.info(absolute_url)
            page = self.plain_session.get(absolute_url)
            assert page.status_code == 200, absolute_url

    def verify_soup(self, context_url, soup):
        for link in soup.find_all('link'):
            assert link.get('href'), link
            self.verify_link(context_url, link.get('href'))
        for link in soup.find_all('a'):
            if link.get('href'):
                self.verify_link(context_url, link.get('href'))
            else:
                assert link.get('name')
            if link.get("img"):
                self.verify_link(context_url, link.get("img"))
                    
        for link in soup.find_all("img"):
            assert link.get("src"), link
            self.verify_link(context_url, link.get("src"))

    def verify(self, url):
        try:
            self.plain_session = requests.Session()
            self.plain_session.mount('file://', FileAdapter())
            logging.info(url)
            resp = self.plain_session.get(url)
            assert resp.status_code == 200, url
            self.verify_soup(url, BeautifulSoup(resp.text, features="lxml"))
            
            self.html_session = HTMLSession()
            self.html_session.mount("file://", FileAdapter())
            logging.info(f"Rendering {url}")
            resp = self.html_session.get(url)
            assert resp.status_code == 200, url
            resp.html.render() # executes javascript, populates resp.html.html
            self.verify_soup(url, BeautifulSoup(resp.html.html, features="lxml"))

            logging.info(f"Verifying strict markup for rendered {url}")
            try:
                etree.parse(io.StringIO(resp.html.html), etree.HTMLParser(recover=False))
            except Exception as e:
                rendered_filename = "verify-rendered.html"
                logging.error(f"""Saving rendered file as {rendered_filename}
$ less -N {rendered_filename}
then enter the line number and press g to go there.""")
                with open(rendered_filename, "w") as outfile:
                    outfile.write(resp.html.html)
                logging.error(e)
                sys.exit(1)
        finally:
            if self.markfile:
                with open(self.markfile, "w") as outfile:
                    json.dump(self.marks, outfile)

def main():
    parser = init_argparse()
    args = parser.parse_args()
    v = Verifier(args.markfile, args.expire)
    v.verify(args.url.strip())

if __name__ == "__main__":
    main()
