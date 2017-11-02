import logging

import html2text
from bs4 import BeautifulSoup
from lazy_property import LazyProperty as lazy_property

logger = logging.getLogger(__name__)


class Article:
    def __init__(self, page):
        self.page = page

    @lazy_property
    def title(self):
        return self._process_html[0]

    @lazy_property
    def content(self):
        return self._process_html[1]

    @lazy_property
    def _process_html(self):
        soup = BeautifulSoup(self.page.text, 'lxml')
        h = html2text.HTML2Text()
        h.body_width = 0  # Otherwise, random `\n` appear.
        div = soup.find('div', {'class': 'postArticle-content'})

        title_html = str(div.h1.getText(separator=' '))
        article_html = str(div.getText(separator=' '))

        title = str(h.handle(title_html)).strip()
        content = str(h.handle(article_html))

        if content.startswith(title):
            content = content[len(title):].strip()
        else:
            logger.info(
                "Article content don't starts with title content: %s, %s.",
                title, content[:2 * len(title)]
            )

        return title, content
