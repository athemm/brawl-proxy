import socket
import time
from threading import *
import json
import sys
from colorama import Fore, Style
from colorama import init
init()


def _(*args):
    print(Fore.LIGHTWHITE_EX + '[INFO]' + Style.RESET_ALL, end=' ')
    for arg in args:
        print(Fore.LIGHTBLUE_EX + arg, end=' ')
    print(Style.RESET_ALL)

def c2s(*args):
    print(Fore.GREEN + '[C -> S]' + Style.RESET_ALL, end=' ')
    for arg in args:
        print(Fore.LIGHTBLUE_EX + arg, end=' ')
    print(Style.RESET_ALL)

def s2c(*args):
    print(Fore.CYAN + '[S -> C]' + Style.RESET_ALL, end=' ')
    for arg in args:
        print(Fore.LIGHTBLUE_EX+ arg, end=' ')
    print(Style.RESET_ALL)

class Server:
    Clients = {"ClientCounts": 0, "Clients": {}}
    ThreadCount = 0

    def __init__(self, ip: str, port: int):
        self.server = socket.socket()
        self.port = port
        self.ip = ip

    def start(self):

        self.server.bind((self.ip, self.port))
        _(f'Proxy started! Ip: {self.ip}, Port: {self.port}')
        while True:
            self.server.listen()
            client, address = self.server.accept()
            _(f'New client! Ip: {address[0]}')
            ClientThread(client, address).start()
            Server.ThreadCount += 1


class ClientThread(Thread):
    def __init__(self, client, address):
        super().__init__()
        self.client = client
        self.address = address
        self.send = socket.socket()
        self.settings = json.loads(open("config.json", "r").read())
        self.send.connect((self.settings["server"], self.settings["port"]))

    def recvall(self, length: int):
        data = b''
        while len(data) < length:
            s = self.client.recv(length)
            if not s:
                print("Receive Error!")
                break
            data += s

        return data

    def run(self):
        last_packet = time.time()
        try:
            while True:
                header = self.client.recv(7)

                if len(header) > 0:
                    last_packet = time.time()
                    packet_id = int.from_bytes(header[:2], 'big')
                    length = int.from_bytes(header[2:5], 'big')
                    data = self.recvall(length)

                    # Replace module
                    if packet_id == 10100:

                        self.settings = json.loads(open("config.json", "r").read())
                        index = 0

                        for Replace in self.settings["ReplaceKeys"]:
                            data = data.replace(Replace.to_bytes(4, 'big'), self.settings["ReplaceVals"][index].to_bytes(4, 'big'))
                            index += 1
                    
                    # Ignore module
                    if packet_id in self.settings["IgnoreC2S"]:
                        c2s("Ignoring client's 'packet id " + Fore.LIGHTYELLOW_EX + str(packet_id) + Style.RESET_ALL);
                        continue

                    # Ignore module
                    if packet_id in self.settings["DoNotAwaitReplyC2S"]:
                        c2s("Not waiting reply for client's 'packet id " + Fore.LIGHTYELLOW_EX + str(packet_id) + Style.RESET_ALL);
                        self.send.send(header + data)
                        continue

                    c2s("Client sends packet id " + Fore.LIGHTYELLOW_EX + str(packet_id) + Style.RESET_ALL + " with length " + Fore.GREEN + str(length) + Style.RESET_ALL)

                    self.send.send(header + data)
                    self.send.settimeout(self.settings["TimeOut"]) # set it to around 2 for avrg internet

                    try:
                        s2c_header = self.send.recv(7)
                        s2c_data = self.send.recv(900000024)
                    except:
                        s2c("Packet id " + Fore.LIGHTYELLOW_EX + str(packet_id) + Style.RESET_ALL + " expired...");
                        continue

                    s2c_packet_id = int.from_bytes(s2c_header[:2], 'big')
                    s2c_length = int.from_bytes(s2c_header[2:5], 'big')

                    if s2c_packet_id in self.settings["IgnoreS2C"]:
                        s2c("Ignoring server's packet id " + Fore.LIGHTYELLOW_EX + str(s2c_packet_id) + Style.RESET_ALL);
                        continue

                    s2c("Server responds packet id " + Fore.LIGHTYELLOW_EX + str(s2c_packet_id) + Style.RESET_ALL + " with length " + Fore.GREEN + str(s2c_length) + Style.RESET_ALL)
                    self.client.send(s2c_header + s2c_data)


                if time.time() - last_packet > 10:
                    _(f"IP Address: {self.address[0]} disconnected!")
                    self.client.close()
                    break

        except ConnectionAbortedError:
            _(f"IP Address: {self.address[0]} disconnected!")
            self.client.close()
        except ConnectionResetError:
            _(f"IP Address: {self.address[0]} disconnected!")
            self.client.close()
        except TimeoutError:
            _(f"IP Address: {self.address[0]} disconnected!")
            self.client.close()


if __name__ == '__main__':
    server = Server('0.0.0.0', 9339)
    server.start()
