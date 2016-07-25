#!/usr/bin/env python3

if __name__ == "__main__":
    import cgi, cgitb, os
    cgitb.enable(display=1, logdir=os.getcwd)
    from core import boot
    boot.boot()
