#!/usr/bin/env python3

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import settings

import argparse

class Rebuild(argparse.Action):
    def __init__(self, option_strings, dest, nargs, **kwargs):
        # if nargs is not None:
            # raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, nargs, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser(description='Command-line interface for {}.'.format(settings.PRODUCT_NAME))
parser.add_argument('-r', action=Rebuild, nargs="+", help='''Rebuilds pages passed as a list. Default is all pages.''')
args = parser.parse_args()
