import logging
import multiprocessing as mp
from itertools import repeat

from src.db import PagesDB
from src.exceptions import FetchError
from src.url import Url
from src.util import DictToSet, DefaultDict
from src.web import Site

logger = logging.getLogger(__name__)


class Validator:
    def __init__(self, m):
        self.used = DictToSet(m.dict())
        self.lock = m.Lock()

    def valid(self, url):
        # with self.lock:
        if url not in self.used:
            self.used.add(url)
            return True
        return False


class Frontier:
    def __init__(self, m):
        self.validator = Validator(m)
        self.queue = m.Queue()

    def put(self, url):
        # This is not perfectly thread-safe, still you can't get to much
        # equal urls in such a short time span.
        if self.validator.valid(url):
            self.queue.put(url)

    def get(self):
        return self.queue.get()

    def done(self):
        return self.queue.task_done()

    def join(self):
        return self.queue.join()


class Crawler:
    def __init__(self, seeds, workers_num=None, al_least_pages=10):
        self.seeds = list(set(map(Url, seeds)))
        self.workers = workers_num or mp.cpu_count()
        self.al_least_pages = al_least_pages

    def run(self):
        # Making a process pool of worker and a manger to share data.
        with mp.Manager() as manager, \
                mp.Pool(processes=self.workers) as pool:
            # Making a shereble frontier using manager.
            frontier = Frontier(manager)
            for seed in self.seeds:
                frontier.put(seed)

            # Create table in advance because it's transaction bottleneck.
            _ = PagesDB()

            # Run procesess in parralel.
            target = self._work
            args = repeat((frontier, self.al_least_pages), self.workers)
            pool.starmap(target, args, chunksize=1)

    @staticmethod
    def _work(frontier, at_least_pages):
        db = PagesDB()
        sites = DefaultDict(default=lambda u: Site(u))

        while db.size() < at_least_pages:
            url = frontier.get()
            site = sites[url]

            if site.allow_crawl(url):
                # Try to fetch an url.
                page = None
                try:
                    page = site.fetch(url)
                except FetchError:
                    logger.warning("Fetch error occured at `%s`.", url)

                # Process page.
                if page is not None:
                    if page.allow_cache:
                        logger.info("Storing page at `%s`.", page.url)
                        db.store(page)

                    for url in page.links:
                        frontier.put(url)

            frontier.done()
