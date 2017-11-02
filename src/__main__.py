import logging

from src.crawler import Crawler

logger = logging.getLogger(__name__)


def parse_seeds():
    return [_[:-1] for _ in open('seeds.txt') if not _.startswith('#')]


if __name__ == '__main__':
    # Set up the logger.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run the crawler.
    # Crawler(parse_seeds(), al_least_pages=100 * 1000 + 1).run()
