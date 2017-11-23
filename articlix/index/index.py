import logging
import multiprocessing as mp
import pickle
import time
from multiprocessing.dummy import Lock

import nltk
import pandas as pd
import ujson
from nltk import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from tqdm import tqdm

logger = logging.getLogger(__name__)

lock = Lock()


class Reverse_index:
    def __init__(self):
        self.index_dict = dict()

    def from_file(self, filename):
        with open(filename, 'rb') as f:
            self.index_dict = pickle.load(f)

    def add_word(self, word, document_id, position, in_title):
        if word not in self.index_dict:
            lock.acquire()
            self.index_dict[word] = dict(
                {document_id: {(position, in_title)}})
            lock.release()
        else:
            if document_id not in self.index_dict[word]:
                lock.acquire()
                self.index_dict[word][document_id] = {(position, in_title)}
                lock.release()
            else:
                lock.acquire()
                self.index_dict[word][document_id].add((position, in_title))
                lock.release()

    def to_file(self, filename):
        def flatten(d):
            return list((k, p, i) for k, v in d.items() for p, i in v)

        fii = {k: flatten(v) for k, v in self.index_dict.items()}

        with open(filename, 'w') as f:
            ujson.dump(fii, f)

    def print(self):
        print("print")
        for word in self.index_dict.keys():
            for document_id in self.index_dict[word].keys():
                print(word, ":\t", document_id,
                      list(self.index_dict[word][document_id]))

    def update(self, new_index):
        if not self.index_dict:
            self.index_dict = dict(new_index.index_dict)
            return
        for word in new_index.index_dict.keys():
            if word in self.index_dict:
                for document_id in new_index.index_dict[word].keys():
                    if document_id in self.index_dict[word]:
                        self.index_dict[word][document_id].union(
                            new_index.index_dict[word][document_id])
                    else:
                        self.index_dict[word][document_id] = set(
                            new_index.index_dict[word][document_id])
            else:
                self.index_dict[word] = dict(new_index.index_dict[word])


def get_tokens(text):
    # get rid of punctuation, stop words and do steming
    tokenizer = RegexpTokenizer(r'\w+')
    stemmer = PorterStemmer()
    tokens = tokenizer.tokenize(text)
    tokens.extend([x + " " + y for x, y in nltk.bigrams(tokens)])
    filtered_tokens = [word for word in tokens if
                       word not in stopwords.words('english')]
    for i in range(len(filtered_tokens)):
        filtered_tokens[i] = stemmer.stem(filtered_tokens[i])
    return filtered_tokens


def _worker(df_str, gi, lock):
    index = Reverse_index()
    id, title, content = df_str

    def add_words(text, is_title):
        for i, word in enumerate(get_tokens(text)):
            index.add_word(word, id, i, is_title)

    add_words(title, True)
    add_words(content, False)

    with lock:
        gi.value += 1

    return index


def build_index(dfpath, indexpath, workers_num=None):
    with mp.Manager() as manager, \
            mp.Pool(processes=workers_num or mp.cpu_count()) as pool:
        print('Read df')
        df = pd.read_hdf(dfpath)

        print('Make args')
        args = []
        gi = manager.Value('i', 0)
        lock = manager.Lock()
        for i, s in tqdm(df.iterrows(), total=len(df)):
            args.append(tuple([(i, s['title'], s['content']), gi, lock]))

        print('Make index')
        result_indexes = pool.starmap_async(_worker, args, chunksize=1)
        with tqdm(total=len(df)) as pbar:
            while gi.value < len(df):
                pred = gi.value
                time.sleep(1)
                after = gi.value
                pbar.update(after - pred)

        print('Collect index')
        final_index = Reverse_index()
        for index in tqdm(result_indexes.get()):
            final_index.update(index)

        print('Serialize index')
        final_index.to_file(indexpath)
