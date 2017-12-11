#!/usr/bin/env python3
import cgi
import pandas as pd
import ujson
from articlix.search.search import Articlix
from articlix.index.index import correct, get_tokens
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import urllib
import numpy as np

def get_tokens_(text, spellcheck):
    tokens = RegexpTokenizer(r'\w+').tokenize(text)
    if spellcheck:
        tokens = [correct(token) for token in tokens]
    return tokens


class Interface:
    def __init__(self):        
        print("Reading data ...")
        df = pd.read_hdf('data/clean_articles.h5')
        ix = ujson.load(open('data/index.json', 'r'))
        self.ss = Articlix(df, ix, spellcheck=False)

    def check_query(self, q):
        inform_str = b''
        q_tokens = get_tokens_(q, False)
        correct_tokens = get_tokens_(q, True)
        need_to_inform = False
        for token, word, correct_token in zip(q_tokens, q.split(' '), correct_tokens):
            if token != correct_token:
                inform_str += b'<b>' + correct_token.encode('utf8') + b'</b> '
                need_to_inform = True
            else:
                inform_str += token.encode('utf8') + b' '
        return ' '.join(correct_tokens), inform_str

    def get_checked_query(self, arguments):
        if 'query' not in arguments:
            return b''
        corrected_query, cor_q_str = self.check_query(arguments['query'].value)
        topn = int(arguments['topn'].value)
        order = arguments['sort_by'].value
        query = arguments['query'].value
        import copy 
        new_args = copy.deepcopy(arguments)
        is_better = self.ss.find(query, topn=topn, order=order, add_scores=True)[0][0] < self.ss.find(corrected_query, topn=topn, order=order, add_scores=True)[0][0]
        if is_better:
            s = b'Do you mean: '
            new_args['query'].value = ' '.join(get_tokens_(new_args['query'].value, True))
            s += b'<a href="http://127.0.0.1:8080/?' + urllib.parse.urlencode({key: new_args[key].value for key in new_args}).encode("utf8") + b'">' + cor_q_str + b'</a>'
            s += b'?<br><br>'
            return s
        return b''

    def get_top_html(self, arguments):
        if 'query' in arguments:
            query = arguments['query'].value
        else:
            query = ''
        if 'priority' in arguments:
            prior = arguments['priority'].value
        else:
            prior = ''
        order = 'scores'
        if 'sort_by' in arguments:
            order = arguments['sort_by'].value
        topn = 5
        if 'topn' in arguments:
            topn = arguments['topn'].value
        return b'''
        <html>
            <head>
                <title>Hello Articlix!</title>
            </head>
            <body>
                <h1> Articlix </h1>
                <form method="get">
                    <label><b>What are you looking for?:</b></label>
                    <br>
                    <input type="text" name="query", size="120"
                    ''' + (b', value="' + query.encode("utf8") + b'"') + b'''> 
                    <br>
                    <br>
                    <label><b> Write about yourself:</b></label>
                    <br>
                    <textarea name="priority" cols="100" rows="3">''' + (prior.encode("utf8")) + b'''</textarea>
                    <br>
                    <br>
                    <label><b>Sort by:</b></label> <br>

                    <select name="sort_by">
                    <option''' + (b' selected' if order == 'scores' else b'') + b''' value="scores">Relevance</option>
                    <option''' + (b' selected' if order == 'published_date' else b'') + b''' value="published_date">Published date</option>
                    <option''' + (b' selected' if order == 'estimate_time' else b'') + b''' value="estimate_time">Estimate time to read</option>
                    <option''' + (b' selected' if order == 'likes' else b'') + b''' value="likes">Number of likes</option>
                    <option''' + (b' selected' if order == 'comments' else b'') + b''' value="comments">Number of comments</option>
                    </select>
                    <br>
                    <br>
                    <label>Show</label>
                    <input type="number" name="topn", size="5"''' + (b', value="' + str(topn).encode("utf8")) + b'''">
                    <label>results.</label>
                    <br>
                    <br>
                    <input type="submit" value="Search!"><br><br><br>
        '''
    def get_start_top_html(self, query=None, prior=None):
        return b'''
        <html>
            <head>
                <title>Hello Articlix!</title>
            </head>
            <body>
                <h1> Articlix </h1>
                <form method="get">
                    <label> Write about yourself:</label>
                    <br>
                    <textarea name="priority" cols="100" rows="3">''' + (prior.encode("utf8") if prior is not None else b'') + b'''</textarea>
                    <br>
                    <input type="submit" value="Continue!">
        '''

    def get_bottom_html(self):
        return b'''
                </form>
            </body>
        </html>
        '''

    def refresh(self, environ, start_response):
        html = self.get_start_top_html() + self.get_bottom_html()

        arguments = cgi.FieldStorage(environ=environ)
        if len(arguments) > 0:
            html = self.get_top_html(arguments) + self.get_checked_query(arguments) + self.get_response_html(arguments) + self.get_bottom_html()

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html]

    def get_response_html(self, arguments):
        query = ''
        prior = ''
        if 'query' in arguments:
            query = arguments['query'].value
        if 'priority' in arguments:
            prior = arguments['priority'].value

        if query == '' or prior == '':
            return self.get_response_to_empty(query == '', prior == '')
        self.ss.priors = prior
        html = b''
        result_list = []
        order = 'scores'
        if 'sort_by' in arguments:
            order = arguments['sort_by'].value
        topn = 5
        if 'topn' in arguments:
            topn = int(arguments['topn'].value)
        return self.create_table(query, self.ss.find(query, topn=topn, order=order))

    def get_article(self, q, doc_id, url, title, content):
        s = b'<a href="' + url.encode('utf8') + b'">' + self.highlight_words(q, title, doc_id, is_title=True) + b'</a>'
        s += b'<dr>'
        s += self.highlight_words(q, content, doc_id, False, get_description=True, window_size=200)
        return s

    def create_table(self, q, pd_table):
        s = b'<table>'
        s += b'<tr><td style="width: 500">Results</td><td>Published date</td><td>Estimated time to read</td><td>Number of likes</td><td>Number of comments</td></tr>'
        for doc_id, row in pd_table.iterrows():
            s += b'<tr>'
            s += b'<td  style="width: 500">' + self.get_article(q, doc_id, row['url'], row['title'], row['content']) + b'</td>'
            s += b'<td>' + str(pd.to_datetime(row['published_date']).date()).encode('utf8') + b'</td>'
            s += b'<td>' + str(row['estimate_time']).encode('utf8') + b'</td>'
            s += b'<td>' + str(row['likes']).encode('utf8') + b'</td>'
            s += b'<td>' + str(row['comments']).encode('utf8') + b'</td>'
            s += b'</tr>'
        s += b'</table>'
        return s

        
    def get_response_to_empty(self, query_is_empty, prior_is_empty):
        s = b''
        if query_is_empty:
            s += b'Please fill query. <br>'
        if prior_is_empty:
            s += b'Please fill info about yourself. <br>'
        return s
    
    def highlight_words(self, query, text, doc_id, is_title, get_description=False, window_size=None):
        positions = []
        for q in get_tokens(query, False):
            for d, pos, is_t in self.ss.index.get(q, []):
                if d == doc_id and is_title == is_t:
                    positions.append(pos)
        positions = np.array(positions)
        frame = ''
        cur_i = 0
        real_i = 0
        real_positions = []
        for i, token in enumerate(get_tokens_(text, False)):
            if token not in stopwords.words('english'):
                if cur_i in positions:
                    real_positions.append(real_i)
                cur_i += 1
            real_i += len(token) + 1
        text = ' '.join(get_tokens_(text, False))
        positions = np.array(real_positions)                
        if len(positions) == 0:
            if get_description and window_size is not None:
                return b'...' + text[:window_size].encode('utf8') + b'...<br>'
            return b'...' + text.encode('utf8') + b'...<br>'

        if not get_description or window_size is None:
            window_size = len(text)
            i_from = 0
        else:
            window_size = min(window_size, len(text))
            i_from = positions[0]
            count = ((i_from < positions) & (positions < i_from + window_size)).sum()
            for i in positions:
                if i + window_size >= len(text):
                    break
                c = ((i <= positions) & (positions < i + window_size)).sum()
                if count < c:
                    count = c
                    i_from = i
        s = b'...'
        i = i_from
        while i < i_from + window_size and i < len(text):
            if i not in positions:
                s += text[i].encode('utf8')
                i += 1
            else:
                s += b'<b>'
                while i < i_from + window_size and text[i].isalpha():
                    s += text[i].encode('utf8')
                    i += 1
                s += b'</b>'
        s += b'...<br>'
        return s

    def run(self):
        try:
            from wsgiref.simple_server import make_server
            httpd = make_server('', 8080, self.refresh)
            print('Serving on http://127.0.0.1:8080...')
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Goodbye.')


