import logging

from articlix.index.index import build_index
from main import parse_args

if __name__ == "__main__":
    args = parse_args()

    # Set up the logger.
    logging.basicConfig(
        level=getattr(logging, args.loglevel, 'WARNING'),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run index building
    build_index(args.dfpath, args.indexpath, args.workers)
