import logging
import re

from lazy_property import LazyProperty as lazy_property

from src.url import Url

logger = logging.getLogger(__name__)


class Source:
    _SEEDS = {}

    def __init__(self):
        assert len(self._SEEDS), "Has to be at least one seed to start with."

    def __call__(self, entry):
        class_name = str(entry.__class__.__name__)
        method_name = 'validate_{}'.format(class_name.lower())
        method = getattr(self, method_name, None)
        return method(entry) if method is not None else False

    @lazy_property
    def seeds(self):
        return set(Url(seed) for seed in self._SEEDS)

    def validate_url(self, url):
        return True

    def validate_site(self, site):
        return True

    def validate_page(self, page):
        return True


class Medium(Source):
    _SEEDS = {
        'https://medium.com',
        'https://medium.com/tag/big-data',
        'https://medium.com/tag/data-science',
        'https://medium.com/tag/machine-learning',
        'https://medium.com/tag/artificial-intelligence',
        'https://medium.com/tag/python',
        'https://medium.com/tag/python3',
        'https://medium.com/tag/python-programming',
        'https://medium.com/tag/coding',
        'https://medium.com/tag/devops',
        'https://medium.com/tag/cloud-computing',
        'https://medium.com/tag/tech'
    }

    def validate_url(self, url):
        return url in self.seeds \
               or self._url_regexp.match(str(url.norm)) is not None

    @lazy_property
    def _url_regexp(self):
        return re.compile(r'https:\/\/medium.com\/'
                          r'(?!tag|p)[@A-Za-z0-9_-]+\/'
                          r'(?!archive|search)[A-Za-z0-9_-]+\Z')


reliable_sources = [
    Medium()
]


class Analyzer:
    def __init__(self, sources):
        self.sources = sources

    def __call__(self, entry):
        return any(source(entry) for source in self.sources)

    def seed(self, url):
        return any(url.norm in source.seeds for source in self.sources)
