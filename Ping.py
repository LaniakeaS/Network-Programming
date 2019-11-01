from socket import *
import argparse
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
total = 0  # Total delay in -n times
min = 1000  # Minimum delay
max = 0  # Maximum delay
hostname = None
sendSuccess = 0
receiveSuccess = 0
lost = 0
lostRate = 0
result = 0
timeoutSetting = 0.0
check = 0


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
        answer = htons(answer) & 0xffff
    else:
        answer = htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID):
    # 1. Wait for the socket to receive a reply
    sendTime = time.time()
    receive = select.select([icmpSocket], [], [], 5)

    if receive == ([], [], []):
        return -2

    # 2. Once received, record time of receipt, otherwise, handle a timeout
    receivePackage, address = icmpSocket.recvfrom(1024)
    receiveTime = time.time()

    # 3. Compare the time of receipt to time of sending, producing the total network delay
    delay = receiveTime - sendTime

    # 4. Unpack the packet header for useful information, including the ID
    receiveICMPHeader = receivePackage[20:28]
    icmpType, icmpCode, receiveChecksum, receiveID, receiveSequence = struct.unpack('bbHHh', receiveICMPHeader)
    receiveICMPData = struct.unpack('d', receivePackage[28:len(receivePackage)])

    # 5. Check that the ID matches between the request and reply
    if icmpType == 3:
        errorHandle = -3 * 10 + icmpCode
        return errorHandle

    if (receiveChecksum - check) != 8:
        return -3

    if ID != receiveID:
        return -1

    # 6. Return total network delay
    global receiveSuccess
    receiveSuccess = receiveSuccess + 1
    return delay


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header
    nowTime = time.time()
    icmpPacket = struct.pack("bbHHhd", ICMP_ECHO_REQUEST, 0, 0, ID, 1, nowTime)

    # 2. Checksum ICMP packet using given function
    theChecksum = checksum(icmpPacket)
    global check
    check = theChecksum

    # 3. Insert checksum into packet
    icmpPacket = struct.pack("bbHHhd", ICMP_ECHO_REQUEST, 0, theChecksum, ID, 1, nowTime)

    # 4. Send packet using socket
    try:
        icmpSocket.sendto(icmpPacket, (destinationAddress, 80))
    except error as e:
        print('Sending error. (%s)' % e)
        exit(-1)

    global sendSuccess
    sendSuccess = sendSuccess + 1


def doOnePing(destinationAddress):
    # 1. Create ICMP socket
    s = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
    ID = os.getpid() & 0xffff

    # 2. Send and receive one ping
    sendOnePing(s, destinationAddress, ID)
    delay = receiveOnePing(s, destinationAddress, ID)
    s.close()

    # 5. Return total network delay
    return delay


def ping(host, timeout):
    # 1. Look up hostname, resolving it to an IP address
    try:
        ipAddress = gethostbyname(host)
    except gaierror as e:
        print('Useless hostname! (%s)' % e)
        exit(-1)

    # 2. Call doOnePing function, approximately every second
    delay = doOnePing(ipAddress)

    # 3. Print out the returned delay
    if delay > 0:
        if delay > timeout:
            delay = delay * 1000
            global receiveSuccess
            receiveSuccess = receiveSuccess - 1
            print('Timeout! (%0.4fms)' % delay)
        else:
            delay = delay * 1000
            print('Get response in %0.4fms.' % delay)
    else:
        if delay == -1:
            print('ID matching failure!')
            exit(-1)
        elif delay == -2:
            print('Unacceptable timeout!')
            exit(-1)
        elif delay == -3:
            print('Checksum inaccurate!')
            exit(-1)
        elif delay == -30:
            print('Network unreachable!')
            exit(-1)
        elif delay == -31:
            print('Host unreachable!')
            exit(-1)
        else:
            print("Unknown error!")
            exit(-1)

    return delay


parser = argparse.ArgumentParser(description='ping')
parser.add_argument('hostname', help='Enter hostname as an argument.')
parser.add_argument('-n', '--n', help='How many times you want to ping. (4 as default)', type=int)
parser.add_argument('-t', '--t', help='Timeout setting. (as second)', type=float)
hostname = parser.parse_args().hostname

if parser.parse_args().n is None:
    pingTime = 4
else:
    pingTime = parser.parse_args().n

if parser.parse_args().t is None:
    timeoutSetting = 1.0
else:
    timeoutSetting = parser.parse_args().t

for i in range(pingTime):
    result = ping(hostname, timeoutSetting)
    total = total + result

    if result > max:
        max = result

    if result < min:
        min = result

lost = sendSuccess - receiveSuccess
avg = total / pingTime
lostRate = lost / sendSuccess * 100
print("\nThe statistical information from %s:" % hostname)
print("    Package: send = %d, receive = %d, lost = %d (lost rate = %d%%)" % (sendSuccess, receiveSuccess, lost, lostRate))

if avg < (timeoutSetting * 1000):
    print("Estimated time of pings (as millisecond):")
    print("    MIN = %0.4fms, MAX = %0.4fms, AVG = %0.4fms" % (min, max, avg))
