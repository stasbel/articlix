import logging

from articlix.crawler.crawler import Crawler
from articlix.crawler.source import Medium
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
    crawler = Crawler(sources=[Medium()],
                      al_least_articles=args.articles,
                      workers_num=args.workers)
    crawler.run()
