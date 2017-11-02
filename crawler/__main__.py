import logging

from crawler.crawler import Crawler
from crawler.source import reliable_sources

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Set up the logger.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run the crawler.
    crawler = Crawler(sources=reliable_sources, al_least_pages=50)
    crawler.run()
