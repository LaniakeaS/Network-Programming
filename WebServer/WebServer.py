from socket import *
import datetime
import argparse


def handleRequest(tcpSocket):
    try:
        try:
            clientSocket, address = tcpSocket.accept()  # Accept the request and extract the socket and address from the client.
        except error as e:
            print(e)
            return

        request = clientSocket.recv(1024)  # Receive client requests using client sockets.
        request = request.decode()  # The request is decoded and converted into a string that is convenient to operate.
        requestList = request.split('\r\n')  # Divide the request into different unit lines, depending on the HTTP format.

        try:
            method, URL, version = requestList[0].split(' ')  # Extract the request method, URL, and version from the first line.

            if method != 'GET':  # Only can deal with method 'GET'
                return

            print('request:\n' + request)
            path = URL[1:]
            statusCode = '200'
            statusInfo = 'OK'
        except ValueError as e:  # If the request is not formatted, 400 HTML files are sent.
            print(address)
            path = '-1'
            file = open('files/400.html', 'r')
            content = file.read()
            version = 'HTTP/1.1'
            statusCode = '400'
            statusInfo = 'Bad Request'

        try:  # Read the file from the hard disk and cache the contents of the file.
            if path != '-1':
                file = open(path, 'r')
                content = file.read()
        except FileNotFoundError as e:  # If the file cannot be found, send an HTML file of 404.
            print('Not found!')
            file = open('files/404.html', 'r')
            content = file.read()
            statusCode = '404'
            statusInfo = 'Not Found'

        # Send the response package to the client based on the HTML response format.
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
        print('response:\n' + response.split('\r\n\r\n')[0])
        response = response.encode()

        try:
            clientSocket.sendall(response)
        except error as e:
            print('Send error!')
            return

        clientSocket.close()
    except BaseException as e2:
        print(e2)
        return


def startServer(serverAddress, serverPort):
    sock = socket(AF_INET, SOCK_STREAM)    # Create the socket needed to connect between the server and the client.
    sock.bind((serverAddress, serverPort))    # Bind the socket to the address of the web server.
    sock.listen(0)    # Listen for possible requests from clients.

    while True:
        handleRequest(sock)    # Use an infinite loop to handle continuous requests from other end systems.


parser = argparse.ArgumentParser(description='WebServer')
parser.add_argument('-p', '--p', help='port', type=int, default=7000)   # The user can run the program from the command line and has the option of manually or automatically configuring the port number.
startServer('10.129.32.71', parser.parse_args().p)    # Start the server.
