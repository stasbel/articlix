# articlix

Information retrieval project at SPbAU 7th term

## Installation

### Dev

We use [pipenv](https://docs.pipenv.org/) as a primary tool for development.  
See [Pipfile](Pipfile), [Pipfile.lock](Pipfile.lock), 
[requirements-dev.txt](requirements-dev.txt) and
[requirements.txt](requirements.txt) for full specification of platform, python
and dependency packages.

### Makefile

We provided [Makefile](Makefile) for convinient commands implementation.  
Run `make help` for get info on that.

### Prerequisites

* **psql>=10.0** for [crawler](articlix/crawler/crawler.py) to store pages

## Usage

We provided [main.py](main.py) script, which implements cli interface.  
Run `python main.py -h` to get info on that.

### Crawler

`python main.py crawler`

### Index

U can now preprocess data (look at [this](articlix/index/clean.ipynb)).  
Then, `python main.py --dfpath="data/clean_articles.h5" --indexpath="data/index.json" --workers=8 index`.

### Web interface

`python main.py web_interface`

Then you can find page on port 8080.

### Data

[Where to find prepared data](data/where.txt)

### Search

[Examples](articlix/search/search.ipynb)

## License

[MIT](LICENSE)
