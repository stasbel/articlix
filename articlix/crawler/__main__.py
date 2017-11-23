import logging

from articlix.crawler.crawler import Crawler
from articlix.crawler.source import Medium
from articlix.crawler.crawler import Analyzer
from articlix.crawler.url import Url
from articlix.crawler.web import Fetcher
from articlix.crawler.article import Article
from main import parse_args

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    args = parse_args()

    # Set up the logger.
    logging.basicConfig(
        level=getattr(logging, args.loglevel, 'WARNING'),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run the crawler.
    crawler = Crawler(sources=[Medium()], al_least_pages=10000, workers_num=8)
    crawler.run()

    # Test
    # analyzer = Analyzer([Medium()])
    # u = Url('https://medium.com/mukuls-random-ramblings/a-new-mayer-in-yahoo-land-12876889b391')
    # p = Fetcher()(u)
    # a = Article(p)
    # print('title:', a.title)
    # print('content:', a.content[:100])
    # print('author:', a.author)
    # print('published time:', a.published_time)
    # print('publisher:', a.publisher)
    # print('estimate time:', a.estimate_time)
    # print('likes:', a.likes)
    # print('tags:', a.tags)
    # print('comments:', a.comments)