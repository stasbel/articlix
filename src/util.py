"""Here is the implementation of stuff related to util funcs."""

import logging
import os

__all__ = ['maybe_mkdir', 'missingdict']

logger = logging.getLogger(__name__)


def maybe_mkdir(dir_name):
    """ Creates seq of dirs.
    :param dir_name: dir to create
    :type dir_name: str
    :return: flag if we actually make something
    :rtype: bool
    """

    # Split dir name into head and tail parts.
    dir_name = dir_name.strip()
    dir_name = dir_name + '/' if dir_name[-1] != '/' else dir_name
    name_head, name_tail = dir_name.split('/', 1)

    # Create head dir if absent.
    do_mk = False
    if not os.path.exists(name_head):
        os.mkdir(name_head)
        logger.info("Make dir %s.", name_head)
        do_mk = True

    # Procced to tail part.
    if len(name_tail):
        os.chdir(name_head)
        logger.info("Chdir to %s.", name_head)
        do_mk = do_mk or maybe_mkdir(name_tail)
        os.chdir('..')
        logger.info("Chdir to top.")

    return do_mk
