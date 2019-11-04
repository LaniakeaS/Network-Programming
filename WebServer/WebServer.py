from socket import *
import datetime
import argparse


def handleRequest(tcpSocket):
    try:
        clientSocket, address = tcpSocket.accept()
    except error as e:
        print(e)
        return

    request = clientSocket.recv(1024)
    request = request.decode()
    requestList = request.split('\r\n')

    try:
        method, URL, version = requestList[0].split(' ')
        path = URL[1:]
        statusCode = '200'
        statusInfo = 'OK'
    except ValueError as e:
        print(address)
        path = '-1'
        version = 'HTTP/1.1'
        statusCode = '400'
        statusInfo = 'Bad Request'
        content = 'Invalid request!'

    try:
        if path != '-1':
            file = open(path, 'r')
            content = file.read()
    except error as e:
        file = open('files/404.html', 'r')
        content = file.read()
        statusCode = '404'
        statusInfo = 'Not Found'

    statusLine = version + ' ' + statusCode + ' ' + statusInfo + '\r\n'
    headerLine1 = 'Connection: close\r\n'
    GMTFormat = '%a, %d %b %Y %H:%M:%S GMT\r\n'
    headerLine2 = 'Date: ' + datetime.datetime.utcnow().strftime(GMTFormat)
    headerLine3 = 'Server: Myself\r\n'
    headerLine4 = 'Last-Modified: NONE\r\n'
    contentLength = str(len(content))
    headerLine5 = 'Content-Length: ' + contentLength + '\r\n'
    headerLine6 = 'Content_Type: text/html\r\n'
    response = statusLine + headerLine1 + headerLine2 + headerLine3 + headerLine4 + headerLine5 + headerLine6 + '\r\n' + content
    response = response.encode()
    clientSocket.sendto(response, address)
    clientSocket.close()


def startServer(serverAddress, serverPort):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((serverAddress, serverPort))
    sock.listen(0)

    while True:
        handleRequest(sock)


parser = argparse.ArgumentParser(description='WebServer')
parser.add_argument('-p', '--p', help='port', type=int, default=8000)
startServer('10.129.32.71', parser.parse_args().p)
