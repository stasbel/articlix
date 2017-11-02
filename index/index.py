import multiprocessing as mp
import pickle
from multiprocessing.dummy import Lock

import nltk
import psycopg2
from nltk import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer

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
                {document_id: set([(position, in_title)])})
            lock.release()
        else:
            if document_id not in self.index_dict[word]:
                lock.acquire()
                self.index_dict[word][document_id] = set(
                    [(position, in_title)])
                lock.release()
            else:
                lock.acquire()
                self.index_dict[word][document_id].add((position, in_title))
                lock.release()

    def to_file(self, filename="reverse_index_file"):
        with open(filename, 'wb') as f:
            pickle.dump(self.index_dict, f)

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


def _worker(raw_from_db):
    index = Reverse_index()
    document_id, _, _, _, document_title, document_text = raw_from_db

    def add_words(text, is_title):
        for i, word in enumerate(get_tokens(text)):
            index.add_word(word, document_id, i, is_title)

    add_words(document_title, True)
    add_words(document_text, False)
    return index


def build_index(db_name="pages", workers_num=None):
    workers = workers_num or mp.cpu_count()
    pool = mp.Pool(processes=workers)

    conn = psycopg2.connect(host='localhost', dbname='postgres',
                            user='postgres')
    conn.set_isolation_level(0)
    args = []

    with conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM {};".format(db_name))
        for record in cur:
            args.append((record,))
    result_indexes = pool.starmap(_worker, args)
    final_index = Reverse_index()
    for index in result_indexes:
        final_index.update(index)
    final_index.print()
    final_index.to_file()
