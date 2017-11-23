import logging
import re
from abc import ABC, abstractmethod

from lazy_property import LazyProperty as lazy_property

from articlix.crawler.url import Url

__all__ = ['Medium', 'Analyzer']

logger = logging.getLogger(__name__)


class _Source(ABC):
    def __init__(self):
        assert len(self.seeds), "Has to be at least one seed to start with."

    def __call__(self, entry):
        class_name = str(entry.__class__.__name__)
        method_name = 'validate_{}'.format(class_name.lower())
        method = getattr(self, method_name, None)
        return method(entry) if method is not None else False

    @property
    @abstractmethod
    def seeds(self):
        pass

    def validate_url(self, url):
        return True

    def validate_site(self, site):
        return True

    def validate_page(self, page):
        return True

    def validate_article(self, article):
        return True


class Medium(_Source):
    # Parsed from medium top 1000 tags
    _TAGS_FILE = 'articlix/crawler/tags.txt'
    _YEARS = set('20{}'.format(str(i).rjust(2, '0')) for i in range(4, 18))

    @lazy_property
    def tags(self):
        with open(self._TAGS_FILE, 'r') as r:
            return set('-'.join(t.split()).lower() for t in r.readlines())

    @lazy_property
    def seeds(self):
        tag_base = Url('medium.com/tag')
        tag_based = set(tag_base + tag for tag in self.tags)
        tag_archive = set(tag_base + f'{tag}/archive' for tag in self.tags)
        tag_years = set(tag + year for tag in tag_archive
                        for year in self._YEARS)
        tag_latest = set(tag_base + f'{tag}/latest' for tag in self.tags)
        topic_base = Url('medium.com/topic')
        topic_based = set(topic_base + tag for tag in self.tags)
        hackernoon = {Url('hackernoon.com')}
        return tag_based | tag_archive | tag_years \
               | tag_latest | topic_based | hackernoon

    def validate_url(self, url):
        return url in self.seeds \
               or self._url_regexp.match(str(url.norm)) is not None \
               or self._blogs_regexp.match(str(url.norm)) is not None

    def validate_article(self, article):
        tags = []
        if article.tags is not None:
            tags = article.tags.split()
        return any(tag in self.tags for tag in tags)

    @lazy_property
    def _url_regexp(self):
        return re.compile(r'https:\/\/medium.com\/'
                          r'(?!tag|p)[@A-Za-z0-9_-]+\/'
                          r'(?!archive|search)[A-Za-z0-9_-]+\Z')

    @lazy_property
    def _blogs_regexp(self):
        return re.compile(r'https:\/\/'
                          r'(hackernoon|(medium|blog|m)\.[A-Za-z0-9]+)'
                          r'\.(com|it|org|co|li)\/'
                          r'(?!tag|p)[@A-Za-z0-9_-]+[-/]?'
                          r'(?!archive|search)[A-Za-z0-9_-]+\Z')
