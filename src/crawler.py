import logging
import multiprocessing as mp
import time
from contextlib import contextmanager
from itertools import repeat

from tqdm import tqdm

from src.db import PagesDB
from src.exception import FetchError
from src.source import Analyzer
from src.web import Site

logger = logging.getLogger(__name__)


class Frontier:
    def __init__(self, m):
        self.queue = m.Queue()
        self.used = m.dict()

    def __len__(self):
        return self.queue.qsize()

    def put(self, url):
        # Ok, this is not process-safe code, but, nevertheless, it's working.
        if url not in self.used:
            self.queue.put(url)
            self.used[url] = None

    @contextmanager
    def get(self):
        # logger.warning("TAKE TASK")
        yield self.queue.get()
        self.queue.task_done()
        # logger.warning("TASK DONE")

    def join(self):
        return self.queue.join()


class Crawler:
    def __init__(self, sources, workers_num=None,
                 table_name='pages', new_table=True,
                 al_least_pages=10):
        self.sources = sources
        self.workers = workers_num
        self.table_name = table_name
        self.new_table = new_table
        self.al_least_pages = al_least_pages

    def run(self):
        # Making a process pool of worker and a manger to share data.
        with mp.Manager() as manager, \
                mp.Pool(processes=self.workers or mp.cpu_count()) as pool:
            # Making a sherable frontier using manager.
            frontier = Frontier(manager)
            for source in self.sources:
                for seed in source.seeds:
                    frontier.put(seed)

            # Making an analyzer for page validating.
            analyzer = Analyzer(self.sources)

            # Create table in advance because it's transaction bottleneck.
            if self.new_table:
                db = PagesDB(self.table_name)
                db.drop()
                db.close()
            PagesDB(self.table_name).close()

            # Run procesess in parrallel.
            target = self._work
            args = repeat(
                (frontier, analyzer, self.table_name, self.al_least_pages),
                self.workers or mp.cpu_count()
            )
            pool.starmap_async(target, args, chunksize=1)

            # Progress bar with sizes check.
            with tqdm(total=self.al_least_pages) as pbar:
                db = PagesDB(self.table_name)
                while db.size() < self.al_least_pages:
                    pred = db.size()
                    time.sleep(1)
                    after = db.size()
                    frontier_size = len(frontier)
                    pbar.set_description("Frontier size is {}, pages stored"
                                         .format(frontier_size))
                    pbar.update(after - pred)
                    if not frontier_size:
                        break

    @staticmethod
    def _work(frontier, analyzer, table_name, at_least_pages):
        # Initial connection to db and sites info.
        db = PagesDB(table_name)
        sites = dict()

        # Continue to work till got enough pages.
        while db.size() < at_least_pages:
            with frontier.get() as url:
                # Fetch url site (with caching) and validate it.
                if url.site not in sites:
                    site = Site(url)
                    sites[url.site] = site
                    if not analyzer(site):
                        continue
                site = sites[url.site]
                if not site.allow_crawl(url):
                    continue

                # Try fetch a page and validate it.
                page = None
                try:
                    page = site.fetch(url)
                except FetchError:
                    logger.warning("Fetch error occured at `%s`.", url)
                if not analyzer(page):
                    continue

                # Process page and validate new.
                if page.allow_cache:
                    db.store(page)
                    logger.info("Store page at `%s`.", page.url)
                for url in page.links_gen():
                    if analyzer(url):
                        frontier.put(url)
