import socket
from pprint import pprint

HOST, PORT = '127.0.0.1', 8080
counter = 0

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)
print ('Serving HTTP on port %s ...' % PORT)
while True:
    counter += 1
    client_connection, client_address = listen_socket.accept()
    request = client_connection.recv(1024)
    print (request)

    http_response = b"""\
    HTTP/1.0 200 OK

    <HTML>
    <HEAD>
    <TITLE>HTTP Homework</TITLE>
    <meta name = "Server" content = "jh5387">
    <meta name = "Content-Length" content = "XXX">
    <meta name = "Content-Type" content = "text/html">
    <meta name = "Connection" content = "Closed">
    </HEAD>

    <BODY>
    <H3><CENTER>HTTP Homework</CENTER></H3>This is the main
    page<P>You can click on <A HREF="/page2">page 2</A> or <A HREF="/page3">or Page
    3</A><P><CENTER>This server has been used {{counter}} times</CENTER></BODY></HTML>

    """

    client_connection.sendall(http_response)
    client_connection.close()
