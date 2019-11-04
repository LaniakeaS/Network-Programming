import socket
import argparse
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
prot = 'icmp'
sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname(prot))
ttl = 1
maxHop = 30
sequence = 0


def checksum(byte):
    csum = 0
    countTo = (len(byte) // 2) * 2
    count = 0

    while count < countTo:
        # thisVal = ord(byte[count+1]) * 256 + ord(byte[count])
        thisVal = byte[count + 1] * 256 + byte[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(byte):
        # csum = csum + ord(byte[len(byte) - 1])
        csum = csum + byte[len(byte) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    if sys.platform == 'darwin':
        answer = socket.htons(answer) & 0xffff
    else:
        answer = socket.htons(answer)

    return answer


def receiving(destAddress, ID, sendTime, timeout):
    receive = select.select([sock], [], [], timeout)

    if receive == ([], [], []):
        print('*    ', end='')
        return -1

    receivePack, address = sock.recvfrom(1024)
    receiveTime = time.time()
    print('%dms   ' % ((receiveTime - sendTime) * 1000), end='')
    receivePack = receivePack[20:36]
    headerType, code, receiveChecksum, receiveID, receiveSequence, data = struct.unpack('bbHHhd', receivePack)

    if headerType == 0:
        return [0, address[0]]

    return address[0]


def sending(destAddress, ID):
    sendTime = [0, 0, 0]
    currentTime = time.time()

    if prot == 'icmp':
        global sequence
        pack = struct.pack('bbHHhd', ICMP_ECHO_REQUEST, 0, 0, ID, sequence, currentTime)
        theChecksum = checksum(pack)
        pack = struct.pack('bbHHhd', ICMP_ECHO_REQUEST, 0, theChecksum, ID, sequence, currentTime)
        sequence += 1
    elif prot == 'udp':
        pass

    for k in range(3):
        try:
            sock.sendto(pack, (destAddress, 80))
        except socket.error as e:
            print('Sending error. (%s)' % e)
            exit(-1)

        sendTime[k] = time.time()

    return sendTime


def Tracert(destAddress, TTL, timeout):
    try:
        ipAddress = socket.gethostbyname(destAddress)
    except socket.gaierror as e:
        print('Useless hostname! (%s)' % e)
        exit(-1)

    try:
        ID = os.getpid() & 0xffff
        sock.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)
    except socket.error as e:
        print(e)
        exit(-1)

    sendTime = sending(ipAddress, ID)
    print('%d    ' % ttl, end='')
    result = None
    isTimeout = False

    for j in range(3):
        result = receiving(ipAddress, ID, sendTime[j], timeout)

        if result == -1:
            isTimeout = True

    if isTimeout:
        print("Request Timeout")
    elif isinstance(result, list):
        if result[0] == 0:
            print(result[1])
            print('Done!')
            exit(0)
    else:
        print(result)


parser = argparse.ArgumentParser(description='traceroute')
parser.add_argument('destAddress', help='Enter address of destination as an argument.')
parser.add_argument('-prot', '--prot', help='Which protocal do you want to use?')
parser.add_argument('-max', '--max', help='Set max hop.', type=int, default=30)
parser.add_argument('-to', '--to', help='Set timeout.', type=int, default=1)

if parser.parse_args().prot is None:
    prot = 'icmp'
else:
    prot = parser.parse_args()

for i in range(parser.parse_args().max):
    Tracert(parser.parse_args().destAddress, ttl, parser.parse_args().to)
    ttl = ttl + 1

print('Done!')
