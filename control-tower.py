#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import time
import threading
import socket
import struct
import select
import json
import random
import string
from math import ceil
from comunication import getConnectionInfo, createMulticastSocket, getOwnLinkLocal
class server:
    def __init__(self):
        os.system("clear")
        self.sendinfo = True
        self.dowork = True
        self.waitclients = True
        self.unicast_connections = []
        self.tcp_socket = None
        group, self.MYPORT = getConnectionInfo("distributed")
        self.multicast_sock, self.addrinfo, self.interface = createMulticastSocket(group, self.MYPORT)
        send_information = threading.Thread( name='send_information', target=self.send_information)
        tcp_thread = threading.Thread( name='tcp_thread', target=self.waitTCPCLients, args=[self.interface])
        tcp_thread.start()
        send_information.start()
        tcp_thread.join(1)
        send_information.join(1)
        self.time_to = []        
        self.climate_conditions = {"Rainy":  int(4 + int(random.choice(string.digits))),
                                   "Sunny":  int(1 + int(random.choice(string.digits))),
                                   "Stormy":  int(6 + int(random.choice(string.digits))),
                                   "Cloudy":  int(2 + int(random.choice(string.digits))),
                                   "Tornado":  int(10 + int(random.choice(string.digits)))}
        self.current_weather = ""
        self.changeWeather()
        self.plane_state = []
        self.turn = -1
        for i in range(2):
            self.plane_state.append(False)
            self.time_to.append(int(3 + int(random.choice(string.digits))))
        
    def send_information(self):
        while self.sendinfo:
            time.sleep(0.5)
            self.sendToGroup("Hi")
        print("Multicast: Sent finished ")
        self.divide_work(0, self.number, len(self.unicast_connections))

    def planeLanding(self, plane, client):
        self.plane_state[0] = True
        self.turn = 0
        #Aqui se le dice que espere
        if self.plane_state[1] and self.turn == 0:
            self.sendToClient(client = client, visible = False, data = json.dumps({"state": "WAIT"}))
     
        while self.plane_state[1] and self.turn == 0:
            pass
        self.beOnLandingTrack(self.turn)
        self.sendToClient(client = client, visible = False, data = json.dumps({"state": "OK"}))
        print("Plane " + plane + " has landed!")
        self.plane_state[0] = False


    def planeTakeOff(self, plane, client):
        self.plane_state[1] = True
        self.turn = 1
        #Aqui se le dice que espere
        if self.plane_state[0] and self.turn == 1:
            self.sendToClient(client = client, visible = False, data = json.dumps({"state": "WAIT"}))
     
        while self.plane_state[0] and self.turn == 1:
            pass
        self.beOnLandingTrack(self.turn)
        self.sendToClient(client = client, visible = False, data = json.dumps({"state": "OK"}))
        print("Plane " + plane + " has taken off!")
        self.plane_state[0] = False


    def changeWeather(self):
        self.current_weather = random.choice(list(self.climate_conditions.keys()))
        print("\033[1;10H" + "Climate condition: " + self.current_weather)
        return self.climate_conditions[self.current_weather]

    def waitTCPCLients(self, interface):
        try:
            addr = socket.getaddrinfo(getOwnLinkLocal(interface) + '%' + interface, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
            self.tcp_socket = socket.socket(addr[0], socket.SOCK_STREAM)
            self.tcp_socket.bind(addr[-1])
            self.tcp_socket.listen(2)
            self.unicast_connections.append(self.tcp_socket)
        except Exception as e:
            print("Error connecting")
            self.tcp_socket.close()

        print ("Waiting for TCP connections, address: '%s'" % str(addr[-1][0]))
        while self.waitclients:
            try:
                conn, address = self.tcp_socket.accept()
                print("Connection stablished with client " + "#" + str(len(self.unicast_connections)) + " " + str(address))
                self.unicast_connections.append(conn)
                ping_client = threading.Thread(name='pingClient', target=self.pingClient, args=[conn, len(self.unicast_connections)])
                new_con = threading.Thread(name='tcpConnection', target=self.tcpConnection, args=[conn])
                new_con.start()
                ping_client.start()
                new_con.join(1)
                ping_client.join(1)
                if len(self.unicast_connections) == 2:
                    self.sendinfo = False
                    for client in self.unicast_connections:
                        self.sendToClient(client = client, visible = False, data = json.dumps({"state": "begin"}))

            except Exception as e:
                print(e)
                self.waitclients = False
        print("Closing connections")

    def pingClient(self, client, number):
        try:
            while self.dowork:
                time.sleep(0.5)
                if client:
                    self.sendToClient(client, "PING", False)
        except Exception as e:
            print("Stop pinging client " + str(number))

    def tcpConnection(self, client):
        data = ""
        try:
            while self.dowork:
                data = client.recv(1024*2)
                if len(data):
                    if "PING" not in data.decode():
                        print('Received from one client:', data)
                        self.checkData(data, client)
        except Exception as e:
            print(e)
        print("Closing connection with gone client")
        client.close()

    def beOnLandingTrack(self, type):
        time.sleep(self.time_to[type] + self.changeWeather())


    def checkData(self, data, client):
        try:
            data = json.loads(data.decode())
            if data["type"] == "0":
                #Aterrizaje
                self.planeLanding(client = client, plane = data["plane"]) 
            elif data["type"] == "1":
                #Despegue
                self.planeTakeOff(client = client, plane = data["plane"]) 
        except Exception as e:
            print(e)
            print("Thats an error :(")

    def sendToClient(self, client, data, visible = True):
        if visible:
            print ('Sending to client :', data)
        client.send(data.encode())

    def sendToGroup(self, message):
        self.multicast_sock.sendto(message.encode(), (self.addrinfo[4][0], self.MYPORT))

if __name__ == "__main__":
    try:
        s = server()
    except Exception as e:
        print(e)
        print("Usage: control-tower.py ")
