import struct
import socket
import binascii
import subprocess
#This just creates the multicast group
def getConnectionInfo(group_name):
    ip = None
    port = None
    if len(group_name) > 5:
        text = (binascii.hexlify(group_name.encode('utf-8')).decode())
        port = int('0x' + text[len(text) - 4:len(text)], 0)
        port = port + 5000
        cafe = 'cafe'
        ip = "ff05"
        index = 0
        lon = len(text)
        if lon > 29:
            text = text[0:28]

        for i in range(1, 29 - lon):
            text += cafe[index]
            index = 0 if not i%4 else index + 1

        for index, i in enumerate(text, start = 0):
            ip += i if index%4 else ':' + i
    return ip, port
def getOwnLinkLocal(interface):
        find_ip = subprocess.Popen('ip addr show ' + interface + ' | grep "\<inet6\>" | awk \'{ print $2 }\' | awk \'{ print $1 }\'', shell=True, stdout=subprocess.PIPE)
        link_local = str(find_ip.communicate()[0].decode('utf-8')).split('/')[0]
        if link_local == '':
            raise ValueError("Error: No IPv6 address for that interface ")
        return link_local
def createMulticastSocket(group, MYPORT):
    # print("\033[0;0H")
    print("Talking to multicast IP: " + group + ", port: " + str(MYPORT))
    addrinfo = socket.getaddrinfo(group, MYPORT)[0]
    # Crea el socket del tipo IPv6
    multicast_sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    # se hace bind en ese puerto
    multicast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # multicast_sock.bind(('', MYPORT))
    interfaces = [i[1] for i in socket.if_nameindex() ]
    for index, int in enumerate(interfaces, start = 0):
        try:
            if(index):
                add = getOwnLinkLocal(int)
                break
        except Exception as e:
            continue
    interface = int
    interface = "docker0" 
    interface_index = socket.if_nametoindex(interface)
    # Unirse al grupo multicast
    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    mreq = struct.pack('@I', interface_index)
    multicast_sock.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_MULTICAST_IF, mreq)
    _group = socket.inet_pton(socket.AF_INET6, group) + mreq
    multicast_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, _group)
    return multicast_sock, addrinfo, interface
