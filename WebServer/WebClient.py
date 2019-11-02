from socket import *


def receiveHTTP(tcpSock):
    receive = tcpSock.recv(1024)
    print(receive.decode())
    tcpSock.close()


def sendHTTPRequest(tcpSock):
    request = 'GET /files/mypage.html HTTP/1.1\r\nCache-Control: max-age=0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: zh-Hans-CN,zh-Hans;q=0.8,en-US;q=0.5,en;q=0.3\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362\r\nAccept-Encoding: gzip, deflate\r\nHost: localhost:8000\r\nConnection: Keep-Alive\r\n\r\n'
    request = request.encode()
    tcpSock.sendall(request)


sock = socket(AF_INET, SOCK_STREAM)
sock.connect(('10.129.32.71', 8000))
sendHTTPRequest(sock)
receiveHTTP(sock)