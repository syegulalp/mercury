#!/usr/bin/env python3

if __name__ == "__main__":
	from core import boot
	import cgi, cgitb, os
	cgitb.enable(display=0, logdir=os.getcwd)
    boot.boot()
