import socket
import argparse
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
ttl = 1    # TTL has an initial value, which defaults to 1
maxHop = 30    # Max hop times, which is 30 as default.
sequence = 0    # Sequence in ICMP packet.


def checksum(byte):
    csum = 0
    countTo = (len(byte) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = byte[count + 1] * 256 + byte[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(byte):
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


def receiving(ID, sendTime, timeout):
    receive = select.select([sock], [], [], timeout)    # Check whether the receiving packet is readable and whether it has timed out badly.

    if receive == ([], [], []):    # If the timeout is serious or unreadable, the exception code -1 is returned and print '*'.
        print('*    ', end='')
        return -1

    receivePack, address = sock.recvfrom(1024)
    receiveTime = time.time()
    print('%dms   ' % ((receiveTime - sendTime) * 1000), end='')
    receivePack = receivePack[20:36]
    headerType, code, receiveChecksum, receiveID, receiveSequence, data = struct.unpack('bbHHhd', receivePack)

    if headerType == 0:
        return [0, address[0]]
    elif headerType == 3:
        if code == 1:
            print('Host Unreachable!')
            exit(-1)
        else:
            print('Other Error!')
            exit(-1)
    elif headerType == 11:
        if code == 0:
            return address[0]
        else:
            print('Other Error!')
            exit(-1)
    else:
        print('Other Error!')
        exit(-1)


def sending(destAddress, ID):
    sendTime = [0, 0, 0]    # Each traceroute takes three pings, so it need to record three times of sending.
    currentTime = time.time()

    # Package headers and data.
    global sequence
    pack = struct.pack('bbHHhd', ICMP_ECHO_REQUEST, 0, 0, ID, sequence, currentTime)
    theChecksum = checksum(pack)
    pack = struct.pack('bbHHhd', ICMP_ECHO_REQUEST, 0, theChecksum, ID, sequence, currentTime)
    sequence += 1

    for k in range(3):    # Send the packet 3 times and recording send time for each.
        try:
            sock.sendto(pack, (destAddress, 80))
        except socket.error as e:
            print('Sending error. (%s)' % e)
            exit(-1)

        sendTime[k] = time.time()

    return sendTime


def Tracert(destAddress, TTL, timeout):
    try:
        ipAddress = socket.gethostbyname(destAddress)    # Gets the IP address based on the domain name and returns invalid domain name information if an error occurs.
    except socket.gaierror as e:
        print('Useless hostname! (%s)' % e)
        exit(-1)

    try:
        ID = os.getpid() & 0xffff    # Set the communication process ID to the identifier in the icmp package.
        sock.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)    # Set the TTL
    except socket.error as e:
        print(e)
        exit(-1)

    sendTime = sending(ipAddress, ID)
    print('%d    ' % ttl, end='')
    result = None
    isTimeout = False

    for j in range(3):
        result = receiving(ID, sendTime[j], timeout)    # Receive three return packages, and record the return results for each.

        if result == -1:    # If one of the three pings times out, the timeout information is printed.
            isTimeout = True

    if isTimeout:
        print("Request Timeout")
    elif isinstance(result, list):
        if result[0] == 0:
            print(result[1])
            print('Done!')
            exit(0)
        else:
            print('Unknown Error!')
            exit(-1)
    else:
        print(result)


parser = argparse.ArgumentParser(description='traceroute')
parser.add_argument('destAddress', help='Enter address of destination as an argument.')
parser.add_argument('-max', '--max', help='Set max hop.', type=int, default=30)
parser.add_argument('-to', '--to', help='Set timeout.', type=float, default=1.0)

for i in range(parser.parse_args().max):    # End the loop when I reaches the maximum number of hops.
    Tracert(parser.parse_args().destAddress, ttl, parser.parse_args().to)
    ttl = ttl + 1    # At the end of each single traceroute, the TTL is increased by one

print('Done!')
