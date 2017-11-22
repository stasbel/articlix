from urllib.parse import urlparse as url_parse, \
    urlunparse as url_unparse, urljoin as url_join

from lazy_property import LazyProperty as lazy_property
from url_normalize import url_normalize


class Url:
    def __init__(self, url_str):
        self._url_str = url_str

    @lazy_property
    def absolute(self):
        return bool(url_parse(self._url_str).netloc)

    @lazy_property
    def norm(self):
        normalized_url = url_normalize(self._url_str)
        parsed_url = url_parse(normalized_url)
        scheme = 'https' \
            if parsed_url.scheme == 'http' \
            else parsed_url.scheme
        netloc = parsed_url.netloc[4:] \
            if parsed_url.netloc.startswith('www.') \
            else parsed_url.netloc
        return Url(url_unparse(
            parsed_url._replace(
                scheme=scheme,
                netloc=netloc,
                query='')
        ))

    @lazy_property
    def site(self):
        return Url('/'.join(str(self.norm).split('/')[:3]) + '/')

    def __add__(self, other):
        return Url(url_join(self._url_str, str(other)))

    def __radd__(self, other):
        return Url(str(other)) + self

    def __str__(self):
        return self._url_str

    def __eq__(self, other):
        return str(self.norm) == str(other.norm)

    def __hash__(self):
        return hash(str(self.norm))
