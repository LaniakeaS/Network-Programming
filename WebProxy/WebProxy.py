from socket import *
import datetime
import argparse


def handleRequest(tcpSocket):
    try:
        try:
            clientSocket, address = tcpSocket.accept()  # Accept the request and extract the socket and address from the client.
            request = clientSocket.recv(1024)  # Receive client requests using client sockets.
        except error as e:
            print(e)
            return

        request = request.decode()  # The request is decoded and converted into a string that is convenient to operate.
        requestList = request.split('\r\n')  # Divide the request into different unit lines, depending on the HTTP format.

        try:
            method, URL, version = requestList[0].split(' ')  # Extract the request method, URL, and version from the first line.

            if method != 'GET':  # Only can deal with method 'GET'
                return

            for i in range(len(requestList)):
                if requestList[i].split(':')[0] == 'Host':
                    host = requestList[i].split(' ')[1]

            ip = host.split(':')[0]
            port = host.split(':')[len(host.split(':')) - 1]
            print('request:\n' + request)
            path = URL[7:].split(host)[1]
            filename = path.split('/')[len(path.split('/')) - 1]
            statusCode = '200'
            statusInfo = 'OK'
        except ValueError as e:  # If the request is not formatted, 400 HTML files are sent.
            print(address)
            path = '-1'
            file = open('proxy/400.html', 'r')
            content = file.read()
            version = 'HTTP/1.1'
            statusCode = '400'
            statusInfo = 'Bad Request'

        try:  # Read the file from the hard disk and cache the contents of the file.
            if path != '-1':
                localPath = 'proxy/' + filename
                file = open(localPath, 'r')
                content = file.read()
        except FileNotFoundError as e:  # If the file is not found, the proxy server makes a request to the remote server.
            print('Not found, proxy requesting......')
            sock2 = socket(AF_INET,
                           SOCK_STREAM)  # A socket used when creating a connection between a proxy server and a remote server.

            try:
                sock2.connect((ip, int(port)))
            except error as e:
                print(e)
                return

            # Rewrite the request and send to the web server.
            request = 'GET ' + path + ' ' + version + '\r\nHost: 10.129.32.71:7000\r\nProxy-Connection: keep-alive\r\nCache-Control: max-age=0\r\nDNT: 1\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7\r\n\r\n'
            sock2.sendall(request.encode())
            receive = sock2.recv(65535)
            sock2.close()
            print('Done! Responding......')
            clientSocket.sendall(receive)
            print('Done!')
            print('response:\n' + receive.decode().split('\r\n\r\n')[0])

            if receive.decode().split('\r\n')[0].split(' ')[1] == '200':  # If target exist, caching.
                print('Caching......\n')

                try:  # Cache the content requested by the client to the proxy server.
                    cacheFile = open(('proxy/' + filename), 'w')
                    cacheContent = receive.decode().split('\r\n\r\n')[1]
                    cacheFile.write(cacheContent)
                except IOError as e:
                    print(e)
                    print('Caching fail!')
                    return

            print('Done!')
            clientSocket.close()
            return

        # Send response when the file that client need is found in local.
        print('Local Found!!')
        print('Sending......')
        statusLine = version + ' ' + statusCode + ' ' + statusInfo + '\r\n'
        headerLine1 = 'Proxy-Connection: keep-alive\r\n'
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
            clientSocket.sendto(response, address)
        except error as e:
            print(e)
            print('Send fail!')
            return

        clientSocket.close()
        print('Done!')
    except BaseException as e2:
        print(e2)
        return


def startProxy(serverAddress, serverPort):
    sock = socket(AF_INET, SOCK_STREAM)  # Create the socket needed to connect between the server and the client.
    sock.bind((serverAddress, serverPort))  # Bind the socket to the address of the web server.
    sock.listen(15)  # Listen for possible requests from clients.

    while True:
        handleRequest(sock)  # Use an infinite loop to handle continuous requests from other end systems.


parser = argparse.ArgumentParser(description='Web Proxy Server')
parser.add_argument('-p', '--p', help='port', type=int, default=8000)    # The user can run the program from the command line and has the option of manually or automatically configuring the port number.
startProxy('127.0.0.1', parser.parse_args().p)    # Start the server.
