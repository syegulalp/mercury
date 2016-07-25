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
parser.add_argument('-b', metavar='blog', default='', nargs="+", help='''Choose one or more blogs to operate on by their ID#s.''')
parser.add_argument('-rb', metavar='blog', action=Rebuild, nargs="+", help='''Rebuilds multiple blogs, specified by ID#s. Default is all blogs.''')
parser.add_argument('-rp', metavar='page', action=Rebuild, nargs="+", help='''Rebuilds pages in a given blog (specified with -b), specified by ID#s. Default is all pages.''')
parser.add_argument('-p', metavar='', default=True, help='''When used with commands that push jobs to the queue (e.g., -rp), jobs are pushed to the queue but the queue will not run automatically.''')
parser.add_argument('-q', metavar='', default=True, help='''Run all jobs currently in the publishing queue.''')
parser.add_argument('-ql', metavar='', default=True, help='''List all jobs currently in the publishing queue.''')
parser.add_argument('-v', metavar='', default=True, help='''Provide verbose output, detailing all push and publishing actions.''')

args = parser.parse_args()
