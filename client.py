#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import threading
import socket
import struct
import json
import random
import string
from comunication import getConnectionInfo, createMulticastSocket
class client:
    def __init__(self, type):
        os.system("clear")
        self.str_plane_type = {0: 'take off', 1: 'landing'}
        if int(type) in list(self.str_plane_type.keys()): 
            self.plane_type = int(type)
            print('Managing airplanes ' + self.str_plane_type[self.plane_type])
            #Connecting
            self.receive_multicast_info = True
            group, self.MYPORT = getConnectionInfo("distributed")
            self.multicast_sock, self.addrinfo, self.interface = createMulticastSocket(group, self.MYPORT)
            self.multicast_sock.bind(('', self.MYPORT))
            self.unicast_connected_to = None
            self.connected = False
            self.dowork = True
            receive_information = threading.Thread( name='receive_information', target=self.receive_information)
            receive_information.start()
            receive_information.join(1)
            #Creating planes
            self.planes = []
            self.plane_creation_time = []
            self.plane_creation_time.append(2)
            self.plane_creation_time.append(int(3 + int(random.choice(string.digits))))
            self.send = True
        else:
            print("Error: " + str(type) + " is not an option")

    def receive_information(self):
        while self.receive_multicast_info:
            data, sender = self.multicast_sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print(str(sender[0]) + ' ' + str(data))
            if not self.connected:
                self.connectToTCPServer(str(sender[0]))
            else:
                print("Already connected to server")

    def idGenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def addPlane(self):
        while self.dowork:
            self.planes.append(self.idGenerator())
            print("New plane wants to " + ("land" if self.plane_type else "take off") + ": " + self.planes[-1])
            time.sleep(random.randrange(self.plane_creation_time[0], self.plane_creation_time[1]))

    def sendPlane(self):
        while self.dowork:
            time.sleep(random.randrange(self.plane_creation_time[0], self.plane_creation_time[1]))
            if len(self.planes) and self.send:
                info_to_send = json.dumps({"type": self.plane_type, "plane": self.planes[0]})
                print("Sending plane " + self.planes[0] + " to control-tower")
                self.sendToServer(data = info_to_send, visible = False, server = self.unicast_connected_to)

    def connectToTCPServer(self, address_to_connect):
        try:
            self.connected = True
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            addr = socket.getaddrinfo(address_to_connect, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
            sock.connect(addr[-1])
            print("✈ Unicast connection with control tower stablished ✈")
            self.unicast_connected_to = sock
            new_con = threading.Thread(name='server', target=self.tcpConnectedTo, args=[sock])
            new_con.start()
            new_con.join(1)
            self.receive_multicast_info = False
        except Exception as e:
            self.connected = False
            print(e, file=sys.stderr)
            print("Error: Perhaps control tower is not listening :(")

    def tcpConnectedTo(self, server):
        try:
            while self.dowork:
                data = server.recv(1024).decode()
                if len(data):
                    if "PING" not in data:
                        print('Received from tower: ', data)
                        self.checkData(data)
        except Exception as e:
            print(e)
            print("Error")
        server.close()

    def checkData(self, data):
        try:
            data = json.loads(data)
            if data["state"] == "begin":
               #Crear hilo que llame a la creación de aviones en la cola
               plane_creator = threading.Thread(name='create_plane', target=self.addPlane)
               plane_creator.start()
               plane_creator.join(1)
               #Crear hilo que envie el avión en [0] al servidor
               plane_sender = threading.Thread(name='create_plane', target=self.sendPlane)
               plane_sender.start()
               plane_sender.join(1)
            elif data["state"] == "OK":
               print("✈  Plane " + self.planes[0] + " has " + ("taken off" if not self.plane_type else "landed" ))
               del self.planes[0]
               self.send = True
            elif data["state"] == "WAIT":
               print("Control tower asking to wait")
               self.send = False
                
        except Exception as e:
            print("Error on checkData")
            print(e)
            #self.sendToServer(self.unicast_connected_to, data, False)


    def sendToServer(self, server, data, visible = True):
        if visible:
            print ('Sending to server :', data)
        try:
            server.send(data.encode())
        except Exception as e:
            print("Error on sendToServer")
            print(e)

if __name__ == "__main__":
    try:
        s = client(sys.argv[1])
    except Exception as e:
        print(e)
        print(sys.exc_info()[-1].tb_lineno)
        print("Usage: client.py")
