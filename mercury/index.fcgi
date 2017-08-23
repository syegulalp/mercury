#!/usr/bin/env python3

if __name__ == "__main__":
    from core import boot
    boot.boot(aux_settings={'SERVER_MODE':'wsgi'})
