import logging

from src.crawler import Crawler
from src.db import PagesDB

logger = logging.getLogger(__name__)


def parse_seeds():
    return open('seeds.txt').read().splitlines()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    db = PagesDB()
    seeds = parse_seeds()
    crawler = Crawler(seeds, db)
    crawler.run()
