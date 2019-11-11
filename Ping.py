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
sendSuccess = 0    # The number of times the program successfully sent packets.
receiveSuccess = 0    # The number of times the program successfully receive packets.
lost = 0    # How many packets are lost.
lostRate = 0    # lost / sendSuccess
result = 0
timeoutSetting = 0.0
check = 0    # checksum


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


def receiveOnePing(icmpSocket, ID):
    # 1. Wait for the socket to receive a reply
    sendTime = time.time()    # Record the sending time after sending is completed.
    receive = select.select([icmpSocket], [], [], 5)    # Check whether the receiving packet is readable and whether it has timed out badly.

    if receive == ([], [], []):    # If the timeout is serious or unreadable, the exception code -2 is returned
        return -2

    # 2. Once received, record time of receipt, otherwise, handle a timeout
    receivePackage, address = icmpSocket.recvfrom(1024)
    receiveTime = time.time()

    # 3. Compare the time of receipt to time of sending, producing the total network delay
    delay = receiveTime - sendTime

    # 4. Unpack the packet header for useful information, including the ID
    receiveICMPHeader = receivePackage[20:len(receivePackage)]
    icmpType, icmpCode, receiveChecksum, receiveID, receiveSequence, receiveICMPData = struct.unpack('bbHHhd', receiveICMPHeader)

    # 5. Check that the ID matches between the request and reply
    if icmpType == 3:
        errorHandle = -3 * 10 + icmpCode
        return errorHandle

    if ID != receiveID:
        return -1

    # 6. Return total network delay
    global receiveSuccess    # After receiving, temporarily increase the number of successful receiving by one
    receiveSuccess = receiveSuccess + 1
    return delay


def sendOnePing(icmpSocket, destinationAddress, ID, sequence):
    # 1. Build ICMP header
    nowTime = time.time()
    icmpPacket = struct.pack("bbHHhd", ICMP_ECHO_REQUEST, 0, 0, ID, sequence, nowTime)

    # 2. Checksum ICMP packet using given function
    theChecksum = checksum(icmpPacket)
    global check
    check = theChecksum

    # 3. Insert checksum into packet
    icmpPacket = struct.pack("bbHHhd", ICMP_ECHO_REQUEST, 0, theChecksum, ID, sequence, nowTime)

    # 4. Send packet using socket
    try:
        icmpSocket.sendto(icmpPacket, (destinationAddress, 80))
    except error as e:
        print('Sending error. (%s)' % e)
        exit(-1)

    global sendSuccess
    sendSuccess = sendSuccess + 1


def doOnePing(destinationAddress, sequence):
    # 1. Create ICMP socket
    s = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
    ID = os.getpid() & 0xffff    # Treat the communication process ID as the identifier in the ICMP package.

    # 2. Send and receive one ping
    sendOnePing(s, destinationAddress, ID, sequence)
    delay = receiveOnePing(s, ID)
    s.close()

    # 5. Return total network delay
    return delay


def ping(host, timeout, sequence):
    # 1. Look up hostname, resolving it to an IP address
    try:
        ipAddress = gethostbyname(host)
    except gaierror as e:
        print('Useless hostname! (%s)' % e)
        exit(-1)

    # 2. Call doOnePing function, approximately every second
    delay = doOnePing(ipAddress, sequence)

    # 3. Print out the returned delay
    if delay > 0:
        if delay > timeout:
            delay = delay * 1000
            global receiveSuccess
            receiveSuccess = receiveSuccess - 1    # A delayed timeout is not a successful acceptance.
            print('Timeout! (%0.4fms)' % delay)
        else:
            delay = delay * 1000
            print('Get response from %s in %0.4fms.' % (ipAddress, delay))
    else:    # Exception handling
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
parser.add_argument('-n', '--n', help='How many times you want to ping. (4 as default)', type=int, default=4)
parser.add_argument('-t', '--t', help='Timeout setting. (as second)', type=float, default=1.0)
hostname = parser.parse_args().hostname
timeoutSetting = parser.parse_args().t
pingTime = parser.parse_args().n

for i in range(pingTime):
    result = ping(hostname, timeoutSetting, i + 1)    # Start ping for n times.
    total = total + result    # To calculate the average delay, it need to calculate the total delay.

    if result > max:    # Find maximum delay..
        max = result

    if result < min:    # Find minimum delay.
        min = result

lost = sendSuccess - receiveSuccess
avg = total / pingTime
lostRate = lost / sendSuccess * 100
print("\nThe statistical information from %s:" % hostname)
print("    Package: send = %d, receive = %d, lost = %d (lost rate = %d%%)" % (sendSuccess, receiveSuccess, lost, lostRate))

if avg < (timeoutSetting * 1000):    # Delay statistics are not displayed if the average delay is greater than the timeout.
    print("Estimated time of pings (as millisecond):")
    print("    MIN = %0.4fms, MAX = %0.4fms, AVG = %0.4fms" % (min, max, avg))
