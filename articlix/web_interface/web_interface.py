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
        df = pd.DataFrame()
        for chunk in  pd.read_hdf('/home/katenos823/articlix/data/clean_articles2.h5', chunksize=3):
            df = pd.concat([df, chunk], ignore_index=True)
        ix = ujson.load(open('/home/katenos823/articlix/data/index2.json', 'r'))
        print("OK")
        self.ss = Articlix(df, ix, spellcheck=False)
        self.out_assessors_file = "/home/katenos823/articlix/out_assessors_file"

    def check_query(self, q):
        inform_str = b''
        q_tokens = get_tokens_(q, False)
        correct_tokens = get_tokens_(q, True)
        need_to_inform = False
        for token, word, correct_token in zip(q_tokens, q.split(' '), correct_tokens):
            if token.lower() != correct_token.lower():
                inform_str += b'<b>' + correct_token.encode('utf8') + b'</b> '
                need_to_inform = True
            else:
                inform_str += token.encode('utf8') + b' '
        if need_to_inform:
            return ' '.join(correct_tokens), inform_str

    def get_checked_query(self, arguments):
        if 'query' not in arguments:
            return b''
        res = self.check_query(arguments['query'].value)
        if res is None:
            return b''
        corrected_query, cor_q_str = res
        topn = int(arguments['topn'].value)
        order = arguments['sort_by'].value
        import copy 
        query = copy.copy(arguments['query'].value)
        new_args = arguments
        not_cor_scores = list(self.ss.find(query, topn=topn, order=order, add_scores=True)['scores'])
        cor_scores = list(self.ss.find(corrected_query, topn=topn, order=order, add_scores=True)['scores'])
        if len(not_cor_scores) == 0 and len(cor_scores) > 0:
            is_better = True
        elif len(cor_scores) == 0 and len(not_cor_scores) > 0:
            is_better = False
        elif len(not_cor_scores) == 0 and len(cor_scores) == 0:
            return b'Nothing was found...'
        else:
            is_better = cor_scores[0] >= not_cor_scores[0]
        if is_better:
            s = b'Do you mean: '
            new_args['query'].value = ' '.join(get_tokens_(new_args['query'].value, True))
            s += b'<a href="http://35.227.117.218/?' + urllib.parse.urlencode({key: new_args[key].value for key in new_args}).encode("utf8") + b'">' + cor_q_str + b'</a>'
            s += b'?<br><br>'
#            arguments['query'] = query.encode("utf8")
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
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
                <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js" integrity="sha384-vFJXuSJphROIrBnz7yo7oB41mKfc8JzQZiCq4NCceLEaO4IHwicKwpJf9c9IpFgh" crossorigin="anonymous"></script>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js" integrity="sha384-alpBpkh1PFOepccYVYDB4do5UnbKysX5WZXm3XxPqe5iKTfUKjNkCk9SaVuEZflJ" crossorigin="anonymous"></script>
                <style type="text/css">
                .checkboxgroup {
                    display: inline-block;
                    text-align: center;
                }
                .checkboxgroup label {
                    display: block;
                }
                </style>
            </head>
            <body>
                <div style="padding: 20px;">
                <h1> Articlix </h1>
                <form name="form_get" method="get">
                    <label><b>What are you looking for?:</b></label>
                    <br>
                    <div class="col-sm-6">
                    <div class="input-group" >
                    <input type="text" name="query" class="form-control" placeholder="Search for..." aria-label="Search for..."''' + (b' value="' + query.encode("utf8") + b'"') + b'''> 
                    <span class="input-group-btn">
                    <input class="btn btn-outline-success" type="submit" value="Search!" name="search">
                    </span>
                    </div></div>
                    <label><b> Write about yourself:</b></label>
                    <br>
                    <div class="col-sm-6>
                    <textarea class="form-control" name="priority" cols="100" rows="3">''' + (prior.encode("utf8")) + b'''</textarea>
                    </div>
                    <br>
                    <div class="container">
                    <div class="row">
                    <div class="col-sm-2">
                    <label><b>Sort by:</b></label>
                    <select name="sort_by" class="custom-select">
                    <option''' + (b' selected' if order == 'scores' else b'') + b''' value="scores">Relevance</option>
                    <option''' + (b' selected' if order == 'published_date' else b'') + b''' value="published_date">Published date</option>
                    <option''' + (b' selected' if order == 'estimate_time' else b'') + b''' value="estimate_time">Estimate time to read</option>
                    <option''' + (b' selected' if order == 'likes' else b'') + b''' value="likes">Number of likes</option>
                    <option''' + (b' selected' if order == 'comments' else b'') + b''' value="comments">Number of comments</option>
                    </select>
                    </div>
                    <div class="col-sm-2">
                    <label><b>Show:</b></label>
                    <select name="topn" class="custom-select">
                    <option''' + (b' selected' if topn == '5' else b'') + b''' value="5">5</option>
                    <option''' + (b' selected' if topn == '10' else b'') + b''' value="10">10</option>
                    <option''' + (b' selected' if topn == '25' else b'') + b''' value="15">15</option>
                    <option''' + (b' selected' if topn == '20' else b'') + b''' value="20">20</option>
                    <option''' + (b' selected' if topn == '50' else b'') + b''' value="50">50</option>
                    </select>
                    <label>results.</label>
                    </div>
                    </div>
                    </div>
                    <br>
                    </div>
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


    def get_response_html(self, get_args, post_args):
        query = ''
        prior = ''
        if 'query' in get_args:
            query = get_args['query'].value
        if 'priority' in get_args:
            prior = get_args['priority'].value

        if query == '' or prior == '':
            return self.get_response_to_empty(query == '', prior == '')
        self.ss.priors = prior
        html = b''
        result_list = []
        order = 'scores'
        if 'sort_by' in get_args:
            order = get_args['sort_by'].value
        topn = 5
        if 'topn' in get_args:
            topn = int(get_args['topn'].value)
        return self.create_table(query, self.ss.find(query, topn=topn, order=order), post_args)

    def get_article(self, q, doc_id, url, title, content):
        s = b'<a href="' + url.encode('utf8') + b'">' + self.highlight_words(q, title, doc_id, is_title=True) + b'</a>'
        s += b'<dr>'
        s += self.highlight_words(q, content, doc_id, False, get_description=True, window_size=200)
        return s

    def create_table(self, q, pd_table, post_args):
        def create_stars(name):
            def star(number):
                is_marked=False
                if str(name) in post_args:
                    if post_args[str(name)].value == str(number):
                        is_marked = True
                bnum = str(number).encode("utf8")
                return b'''<div class="checkboxgroup">
    <label for="my_radio_button_id''' + bnum + b'''">''' + bnum + b'''</label>
    <input type="radio" name="''' + name.encode("utf8") + b'" id="my_radio_button_id' + bnum + b'" value="' + bnum + (b'" checked' if is_marked else b'"') + b''' />
</div>\n'''
            return b'''<div id="checkboxes">\n''' + star(1) + star(2) + star(3) + star(4) + star(5) + b'''<br><br><br></div>'''
            
        s = b'</form><form name="form_post" method="post"><div style="padding: 20px;"><table class="table table-striped">'
        s += b'<thead><tr><th style="width: 700">Results</th><th style="width: 120">Assessions</th><th style="width: 120">Published date</th><th style="width: 120">Estimated time to read</th><th style="width: 120">Number of likes</th><th style="width: 150">Number of comments</th></tr></thead>'
        topn = len(list(pd_table.iterrows())) - 1
        for i, (doc_id, row) in enumerate(pd_table.iterrows()):
            s += b'<tr>'
            s += b'<td  style="width: 700">' + self.get_article(q, doc_id, row['url'], row['title'], row['content']) + b'</td>'
            s += b'<td  style="width: 120">' + create_stars("radio" + str(i)) + (b'''<input type="submit" name="but_all" class="btn btn-outline-secondary" value="Assess all">''' if i == topn and not post_args else (b'<b>Thanks!</b>' if i == topn and post_args else b'')) + b'</td>'
            s += b'<td  style="width: 120">' + str(pd.to_datetime(row['published_date']).date()).encode('utf8') + b'</td>'
            s += b'<td  style="width: 120">' + str(row['estimate_time']).encode('utf8') + b'</td>'
            s += b'<td  style="width: 120">' + str(row['likes']).encode('utf8') + b'</td>'
            s += b'<td  style="width: 120">' + str(row['comments']).encode('utf8') + b'</td>'
            s += b'</tr>'
        s += b'</table></div>'
        return s

        
    def get_response_to_empty(self, query_is_empty, prior_is_empty):
        s = b''
        if query_is_empty:
            s += b'Please, fill query. <br>'
        if prior_is_empty:
            s += b'Please, fill info about yourself. <br>'
        return s
    

    def highlight_words(self, query, text, doc_id, is_title, get_description=False, window_size=None):
        positions = []
        for i, q in get_tokens(query, False):
            for d, pos, is_t in self.ss.index.get(q, []):
                if d == doc_id and is_title == is_t:
                    positions.append(pos)
        positions = np.array(positions)             
        if len(positions) == 0:
            if get_description and window_size is not None:
                return text[:window_size].encode('utf8') + b'<br>'
            return text.encode('utf8') + b'<br>'

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
        s = b''
        i = i_from
        while i < i_from + window_size and i < len(text):
            if i not in positions:
                s += text[i].encode('utf8')
                i += 1
            else:
                s += b'<b>'
                while i < i_from + window_size and i < len(text) and text[i].isalpha():
                    s += text[i].encode('utf8')
                    i += 1
                s += b'</b>'
        s += b'<br>'
        return s

    def get_client_address(self, environ):
        try:
            return environ['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
        except KeyError:
            return environ['REMOTE_ADDR']

    def remember_assession(self, client, post_args, get_args):
        with open(self.out_assessors_file, 'a') as out:
            topn = int(get_args['topn'].value)
            for pressed_pos in range(topn):
                if 'radio' + str(pressed_pos) in post_args:
                    print(client, get_args['query'].value, get_args['priority'].value, get_args['sort_by'].value, pressed_pos, post_args['radio' + str(pressed_pos)].value, sep='\t', file=out)

    def refresh(self, environ, start_response):
        html = self.get_start_top_html() + self.get_bottom_html()
        get_args = cgi.FieldStorage(environ=environ)
        post_args = {}
        if environ['REQUEST_METHOD'] == 'POST':
            post_env = environ.copy()
            post_env['QUERY_STRING'] = ''
            post_args = cgi.FieldStorage(fp=environ['wsgi.input'], environ=post_env)
            self.remember_assession(self.get_client_address(environ), post_args, get_args)
        if len(get_args) > 0:
            html = self.get_top_html(get_args) + self.get_checked_query(get_args) + self.get_response_html(get_args, post_args) + self.get_bottom_html()

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html]

    def run(self):
        
        try:
            from wsgiref.simple_server import make_server
            httpd = make_server('0.0.0.0', 5000, self.refresh)
            print('Serving...')
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Goodbye.')


