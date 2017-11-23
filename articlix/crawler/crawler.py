import logging
import multiprocessing as mp
import time
import traceback
from contextlib import contextmanager
from itertools import repeat

from tqdm import tqdm

from articlix.crawler.db import PagesDB
from articlix.crawler.exception import FetchError
from articlix.crawler.web import Site

logger = logging.getLogger(__name__)


class Frontier:
    def __init__(self, m):
        self.queue = m.Queue()
        self.used = m.dict()

    def __len__(self):
        return self.queue.qsize()

    def put(self, url, cnt=2, timeout=1):
        # Ok, this is not process-safe code, but, nevertheless, it's working.
        if url not in self.used:
            # self.queue.put((url, cnt))
            # self.used[url] = None
            try:
                self.queue.put((url, cnt), timeout=timeout)
                self.used[url] = None
            except:
                logger.error('Queue put timeout')
                pass

    @contextmanager
    def get(self, timeout=1):
        # yield self.queue.get()
        # self.queue.task_done()
        nxt = None
        while nxt is None:
            try:
                nxt = self.queue.get(timeout=timeout)
            except:
                logger.error('Queue get timeout')
                pass
        yield nxt
        try:
            self.queue.task_done()
        except:
            logger.error('Task done error')
            pass

    def join(self):
        return self.queue.join()


class Analyzer:
    def __init__(self, sources):
        self.sources = sources

    def __call__(self, entry):
        return any(source(entry) for source in self.sources)

    def is_seed(self, url):
        return any(url.norm in source.seeds for source in self.sources)


class Crawler:
    def __init__(self, sources, workers_num=None,
                 table_name='pages', new_table=True, al_least_articles=10):
        self.sources = sources
        self.workers = workers_num
        self.table_name = table_name
        self.new_table = new_table
        self.al_least_pages = al_least_articles

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
                    processes = len(mp.active_children()) - 1
                    desc = f"frontier size is {frontier_size}, " \
                           f"processes number is {processes}, " \
                           "pages stored"
                    pbar.set_description(desc)
                    pbar.update(after - pred)
                    if not frontier_size:
                        break

    @staticmethod
    def _work(*args):
        try:
            work(*args)
        except Exception as e:
            logger.error('Fatal process error `%s`', e)
            traceback.print_exc()


def work(frontier, analyzer, table_name, at_least_pages):
    # Initial connection to db and sites info.
    db = PagesDB(table_name)
    sites = dict()

    # Continue to work till got enough pages.
    while db.size() < at_least_pages:
        with frontier.get() as urlcnt:
            # Process url and cnt
            url, cnt = urlcnt

            # Site
            if url.site not in sites:
                site = Site(url)
                sites[url.site] = site
            else:
                site = sites[url.site]
            try:
                if not site.allow_crawl(url) or not analyzer(site):
                    continue
            except:
                logger.warning('Site error occured at `%s`.', url)
                continue

            # Page
            page = None
            try:
                page = site.fetch(url)
            except FetchError:
                if not analyzer.is_seed(url):
                    logger.warning('Fetch error occured at `%s`.', url)
                continue
            if not analyzer(page):
                continue

            # Article
            is_good = False
            if page.allow_cache and not analyzer.is_seed(url):
                try:
                    article = page.read()
                except Exception as e:
                    continue

                if analyzer(article):
                    db.store(article)
                    is_good = True

            # New links
            cnt = 2 if is_good else cnt - 1
            for url in page.links_gen():
                if cnt > 0 and analyzer(url):
                    frontier.put(url, cnt)
