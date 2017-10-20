import logging
import time
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from lazy_property import LazyProperty as lazy_property

from src.exceptions import FetchError
from src.url import Url

logger = logging.getLogger(__name__)

USER_AGENT = "crawler"


class Page:
    def __init__(self, url, head, text):
        self.url = url
        self.head = head
        self.text = text

    def _head_field(self, field):
        if field in self.head:
            return self.head[field]
        return None

    @lazy_property
    def date(self):
        date = self._head_field('Date')
        if date is not None:
            date = date_parser.parse(date)
        return date

    @lazy_property
    def last_modified(self):
        last_modified = self._head_field('Last-Modified')
        if last_modified is not None:
            last_modified = date_parser.parse(last_modified)
        return last_modified

    @lazy_property
    def _soup(self):
        return BeautifulSoup(self.text, 'html.parser')

    def _have_perm(self, perm):
        for tag in self._soup.find_all('ROBOTS', 'meta'):
            if perm in tag['content'].split(', '):
                return True
        return False

    @lazy_property
    def allow_follow(self):
        return not self._have_perm('NOFOLLOW')

    @lazy_property
    def allow_cache(self):
        return not self._have_perm('NOCACHE')

    @lazy_property
    def links(self):
        urls = []
        if self.allow_follow:
            for link_node in self._soup.find_all('a'):
                url_str = link_node.get('href')
                if url_str is not None:
                    url = Url(link_node.get('href'))
                    urls.append(url if url.absolute else self.url + url)
        return urls


class Fetcher:
    def __init__(self, delay=None, use_adaptive=True, adaptive_scale=3):
        self.delay = delay
        self.use_adaptive = use_adaptive
        self.adaptive_scale = adaptive_scale

        self._last_fetched = None
        self._t = None

    @staticmethod
    def fetch_raw(url):
        try:
            conn = urlopen(
                Request(str(url), headers={'User-Agent': USER_AGENT})
            )
            return dict(conn.info()), conn.read().decode('utf-8')
        except Exception as e:
            raise FetchError('Failed to get data') from e

    def fetch(self, url):
        if self._last_fetched is not None:
            time_passed = time.time() - self._last_fetched

            if self.delay is not None:
                time.sleep(max(self.delay - time_passed, 0))

            if self.delay is None and self.use_adaptive:
                time.sleep(max(self.adaptive_scale * self._t - time_passed, 0))

        self._t = time.time()
        header, content = self.fetch_raw(url)
        self._last_fetched = time.time()
        logging.info("Last fetched time is `%s`.", self._last_fetched)
        self._t = self._last_fetched - self._t

        return Page(url, header, content)


class Site:
    def __init__(self, url):
        self.url = url

    @lazy_property
    def _robots(self):
        robots = RobotFileParser()

        robots_raw = None
        try:
            _, robots_raw = Fetcher.fetch_raw(self.url.site + '/robots.txt')
        except FetchError:
            pass

        if robots_raw is not None:
            robots.parse(robots_raw.splitlines())

        return robots

    def allow_crawl(self, url):
        return self._robots.can_fetch(USER_AGENT, str(url))

    @lazy_property
    def _fetcher(self):
        crawl_delay = None

        try:
            crawl_delay = self._robots.crawl_delay(USER_AGENT)
        except:
            pass

        if crawl_delay is None:
            try:
                request_rate = self._robots.request_rate(USER_AGENT)
                crawl_delay = request_rate[1] / request_rate[0]
            except:
                pass

        return Fetcher(crawl_delay)

    def fetch(self, url):
        return self._fetcher.fetch(url)
