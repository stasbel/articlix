import logging

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
    # crawler = Crawler(sources=reliable_sources, al_least_pages=50)
    # crawler.run()
