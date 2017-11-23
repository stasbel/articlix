import logging
from _datetime import datetime

import dateparser
import html2text
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Article:
    def __init__(self, page):
        self.page = page

        self._soup = BeautifulSoup(self.page.text, 'lxml')
        self.title, self.content = self._parse()
        self.author = self._get_meta('author')
        self.published_time = self._get_meta('article:published_time')
        self.publisher = self._get_meta('article:publisher')
        self.estimate_time = self._estimate_time()
        self.likes = self._likes()
        self.tags = self._tags()
        self.comments = self._comments()

    def _parse(self):
        h = html2text.HTML2Text()
        h.body_width = 0
        div = self._soup.find('div', {'class': 'postArticle-content'})
        title = str(h.handle(str(div.h1.getText(separator=' ')))).strip()
        content = str(h.handle(str(div.getText(separator=' '))))
        if content.startswith(title):
            content = content[len(title):].strip()
        return title, content

    def _get_meta(self, property):
        node = self._soup.find('meta', property=property)
        return node['content'] if node is not None else None

    def _estimate_time(self):
        time = None
        node = self._soup.find('span', {'class': 'readingTime'})
        if node is not None:
            date = dateparser.parse(node['title'][:-5])
            time = int((datetime.now() - date).seconds)
        return time

    def _likes(self):
        likes = None
        class_text = 'button button--chromeless u-baseColor--buttonNormal ' \
                     'js-multirecommendCountButton'
        node = self._soup.find('button', {'class': class_text})
        if node is not None:
            text = node.getText()
            m = 1
            for c in text:
                if c == 'K': m *= 1000
                if c == 'M': m *= 1000 * 1000
            text = ''.join(list((c for c in text if c.isdigit() or c == '.')))
            b, _, a = text.partition('.')
            likes = int(b)
            if len(a): likes += int(a) / (10 ** len(a))
            likes = int(likes * m)
        return likes or 0

    def _tags(self):
        def tags_gen():
            try:
                for ultag in self._soup.find_all('ul', {'class': 'tags'}):
                    for litag in ultag.find_all('li'):
                        yield '-'.join(litag.text.lower().split())
            except:
                pass

        tags = ' '.join(tags_gen())
        if not len(tags): tags = None
        return tags

    def _comments(self):
        comments = None
        class_text = 'button button--chromeless u-baseColor--buttonNormal'
        node = self._soup.find('button', {'class': class_text})
        if node is not None:
            digits = filter(lambda c: c.isdigit(), node.getText())
            comments = int(''.join(digits))
        return comments or 0
