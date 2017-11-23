import argparse

from runpy import run_module
import multiprocessing as mp

__all__ = ['parse_args']


def _pick_magic():
    return {k: _ for k, _ in globals().items() if k.startswith('__')}


_DEFAULT_MAGIC = _pick_magic()

# New magic
__prog__ = 'Articlix'
__desc__ = f'{__prog__} stages'
__version__ = '0.0.1'


def parse_args():
    parser = argparse.ArgumentParser(prog=__prog__,
                                     description=__desc__,
                                     add_help=False)
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}',
                        help="Show program's version number and exit.")
    parser.add_argument('-h', '--help', action='help',
                        default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    parser.add_argument('tasks', metavar='T', type=str,
                        nargs='+', help='Task to run')

    class UpperAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, 'loglevel', values.upper())

    parser.add_argument('--loglevel', dest='loglevel', type=str,
                        default='WARNING', action=UpperAction,
                        help='Set logging level (default: %(default)s).')
    parser.add_argument('--dfpath', dest='dfpath', type=str,
                        help='Path to df')
    parser.add_argument('--indexpath', dest='indexpath', type=str,
                        help='Path for index to save at')
    parser.add_argument('--workers', dest='workers',
                        type=int, default=mp.cpu_count(),
                        help='Number of workers to work in parallel')
    parser.add_argument('--articles', dest='articles',
                        type=int, default=10000,
                        help='Minumin number of atricles to crawl')
    return parser.parse_args()


if __name__ == '__main__':
    init_globals = {k: _ for k, _ in _pick_magic().items()
                    if k not in _DEFAULT_MAGIC}
    for task in parse_args().tasks:
        run_module(f'articlix.{task}', init_globals=init_globals,
                   run_name='__main__', alter_sys=True)
