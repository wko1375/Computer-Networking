#! /usr/bin/env python3

import logging
import multiprocessing as mp
import os
import socket

logging.basicConfig(format='[%(levelname)s <> %(name)s] %(message)s',level=logging.DEBUG,)
logger = logging.getLogger(__name__)

BUFFER_SIZE = 1024

STATUS_MESSAGES = {
    200: 'OK',
    404: 'Not Found',
    405: 'Method Not Allowed',
    500: 'Internal Server Error',
}

PAGES = {
    '/': (
        '<!doctype html>'
        '<html><head><title>HTTP Homework</title></head>'
        '<body><h3><center>HTTP Homework</center></h3>This is the mainpage'
        '<p>You can click on <a href="/page2">page 2</a> or '
        '<a href="/page3">or Page 3</a><p>'
        '<center>This server has been used {count} times</center>'
        '</body></html>'),
    '/page2': (
        '<!doctype html>'
        '<html><head><title>HTTP Homework</title></head>'
        '<body><h3><center>HTTP Homework</center></h3>This is page'
        '2<p>You can go <a href="/">back</a><p>'
        '<center>This server has been used {count} times</center>'
        '</body></html>'),
    '/page3': (
        '<!doctype html>'
        '<html><head><title>HTTP Homework</title></head>'
        '<body><h3><center>HTTP Homework</center></h3>This is page'
        '3<p>You can go <a href="/">back</a><p>'
        '<center>This server has been used {count} times</center>'
        '</body></html>'),
}


class Request:
    def __init__(self, conn):
        self.conn = conn
        self.http_version = None
        self.method = None
        self.path = None
        self.header = {}
        self.metadata = None
        self.body = None
        self.metadata_list = []
        self.body_list = []
        self.timeout = False

        while True:
            try:
                rec = conn.recv(BUFFER_SIZE)
            except socket.timeout as except:
                logger.debug(f'Timed out, closing connection')
                self.conn.send(b'')
                self.conn.close()
                self.timeout = True
                return

            logger.debug(f'Received: {rec}')
            self.metadata_list.append(rec)

            if len(rec) < BUFFER_SIZE:
                logger.debug('Received all data, continuing')
                break

        self.metadata = b''.join(self.metadata_list).decode()

        lines = self.metadata.split('\r\n')

        reqs = lines[0].split(' ')
        self.method = reqs[0]
        self.path = reqs[1]
        self.http_version = reqs[2]

        for line in lines[1:]:
            if line:
                header = line.split(': ')
                self.header[header[0]] = ': '.join(header[1:])

            else:
                break

        if self.header.get('Content-Length', None):
            length = int(self.header['Content-Length'])

            while True:
                to_receive = min(length, BUFFER_SIZE)
                self.body_list.append(conn.recv(to_receive))
                length -= to_receive
                if length <= 0:
                    break

            self.body = b''.join(self.body_list).decode()


class Response:
    def __init__(
        self, conn, code = 200, header = {}, http_version = 'HTTP/1.1', body = ''
    ):
        self.conn = conn
        self.http_version = http_version
        self.code = code
        self.header = header
        self.body = body

    def send(self, data):
        self.body = data
        self.conn.send(self.form())

    def form(self):
        resp = [f'{self.http_version} {self.code} {STATUS_MESSAGES[self.code]}\r\n',]
        self.header['Content-Length'] = len(self.body)
        for k, v in self.header.items():
            resp.append(f'{k}: {v}\r\n')
        resp.append('\r\n')
        resp.append(self.body)
        return ''.join(resp).encode()

    @staticmethod
    def wrap_html(data):
        return (f'<!doctype html><html><head></head>'f'<body>{data}</body></html>')

def handler(conn, count):
    conn.settimeout(1)

    try:
        req = Request(conn)
        if req.timeout:
            return
        code = 200
        if req.method != 'GET':
            code = 405
        if req.path not in PAGES:
            code = 404
    except Exception as e:
        logger.debug(f'Caught: {e}')
        code = 500
    resp = Response(
        conn,
        code = code,
        header = {'Server': 'js8460','Content-Type': 'text/html','Connection': 'Closed',},
    )
    if resp.code == 200:
        resp.send(PAGES[req.path].format(count=count))
    else:
        resp.send(Response.wrap_html(STATUS_MESSAGES[resp.code]))

    conn.close()


def main(sock):
    count = 0

    def _success(_):
        nonlocal count
        logger.info(f'Processed request {count}')

    def _error(e):
        logger.error(f'Processing connection failed: {e}')

    with mp.Pool(
        processes = os.cpu_count(),
        # maxtasksperchild=1,
    ) as pool:
        while True:
            conn, addr = sock.accept()
            logger.info(f'Connection accepted from {addr[0]}:{addr[1]}')
            pool.apply_async(
                args = (conn, count),
                callback = _success,
                func = handler,
                error_callback = _error,
            )

            count += 1


if __name__ == '__main__':
    try:
        sock = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        # sock.bind(('127.0.0.1', 8080))
        sock.bind(('0.0.0.0', 8080))
        sock.listen()
        main(sock)
    finally:
        sock.close()
