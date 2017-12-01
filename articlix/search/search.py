import math
import sys
from functools import lru_cache

import numpy as np

sys.path.append("..")
from articlix.index.index import get_tokens


class Articlix:
    def __init__(self, meta, index,
                 priors=None, spellcheck=True,
                 k1=2.0, b=0.75, p=0.25,
                 idf_do_max=True, idf_smooth=0.5, tf_do_log=False,
                 score_treshold=0.05):
        self.meta = meta
        self.index = index
        self.priors = priors or []
        self.spellcheck = spellcheck
        self.k1 = k1
        self.b = b
        self.p = p
        self.idf_do_max = idf_do_max
        self.idf_smooth = idf_smooth
        self.tf_do_log = tf_do_log
        self.score_treshold = score_treshold

        self.N = len(self.meta)
        self.c1 = self.k1 + 1
        dls = (meta.ttitle_len + meta.tcontent_len).as_matrix()
        self.c2 = self.k1 * ((1 - b) + b * dls / np.mean(dls))
        self.prior_scores = sum(self._scores(prior, False)
                                for prior in self.priors)

    @lru_cache(maxsize=1024)
    def find(self, q, *, topn=5, add_scores=False, order=None):
        # Combine with spellchecking
        if self.spellcheck:
            wos = self._scores(q, False)
            ws = self._scores(q, True)
            q_scores = np.maximum(wos, ws)
        else:
            q_scores = self._scores(q, False)

        # Combine with priors scores
        if len(self.priors):
            scores = (1 - self.p) * q_scores + self.p * self.prior_scores
        else:
            scores = q_scores

        # Get topn and filter out with the treshold
        topn = min(topn, self.N)
        rank = np.argpartition(scores, -topn)[-topn:]
        rank = rank[scores[rank] >= self.score_treshold]

        # Sort accoeding to order
        subdf = self.meta.iloc[rank].copy()
        subdf['scores'] = scores[subdf.index]
        if order is None:
            order = 'scores'
        if isinstance(order, str):
            by, ascending = order, False
        else:
            by, ascending = order[0], order[1] == 'asc'
        subdf.sort_values(by, ascending=ascending, inplace=True)

        # Return all info maybe with scores
        urls = subdf.url.tolist()
        if add_scores:
            return list(zip(subdf.scores, subdf))
        else:
            return subdf

    def _scores(self, q, spellcheck):
        vecs = []
        for t in get_tokens(q, spellcheck):
            idf = self._idf(t)
            tf = self._tf_vec(t)
            vecs.append(idf * ((self.c1 * tf) / (self.c2 + tf)))
        return np.sum(np.stack(vecs), axis=0)

    @lru_cache(maxsize=1024)
    def _idf(self, t):
        df = len(set(_[0] for _ in self.index.get(t, [])))
        if df:
            if self.idf_do_max:
                top = self.N - df + self.idf_smooth
                bot = df + self.idf_smooth
                idf = top / bot
                if idf <= 0:
                    idf = 0
                else:
                    idf = max(0, math.log(idf))
            else:
                top = self.N
                bot = df
                idf = top / bot
                if idf <= 0:
                    idf = 0
                else:
                    idf = math.log(idf)
        else:
            idf = 0
        return idf

    @lru_cache(maxsize=1024)
    def _tf_vec(self, t):
        tf = np.zeros(self.N)
        for d, _, _ in self.index.get(t, []):
            tf[d] += 1
        if self.tf_do_log:
            tf[tf > 0] = 1 + np.log(tf[tf > 0])
        return tf
