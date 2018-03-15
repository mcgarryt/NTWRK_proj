import socket
import sys
import time
import ast
import select
# REFERENCE WEBSITES
## THREADING AND SOCKETING
# https://gist.github.com/micktwomey/606178
# https://eli.thegreenplace.net/2011/05/18/code-sample-socket-client-thread-in-python
# https://docs.python.org/3/howto/sockets.html
# https://stackoverflow.com/questions/1894269/convert-string-representation-of-list-to-list-in-python
FLAG = str(sys.argv[1])
LOCALHOSTNAME = socket.gethostname()
LOCALPORT = sys.argv[2]
POCNAME = socket.gethostbyname(str(sys.argv[3]))
POCPORT = sys.argv[4]
N = int(sys.argv[5])

class Ringo:
    def __init__(self, flag, localhostname, localport, pocname, pocport, n):
        self.flag = flag
        self.localhostname = localhostname
        self.localport = localport
        self.pocname = pocname
        self.pocport = pocport
        self.n = n
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.knownlist = []
        self.knownlist.append((LOCALHOSTNAME,LOCALPORT))
        self.knownlist.append((POCNAME, POCPORT))

        self.newlist = []

    def peer_discovery_send(self, POCNAME, POCPORT):
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = 'PEER' + str(knownlist)
        self.s.sendto(packet.encode(),(POCNAME,POCPORT))
        print("Sending packet: ",packet)
        self.s.setblocking(0)

        while True:
            ready = select.select([self.s],[],[],2)
            if ready[0]:
                data = s.recv(1024)
                break;
            else:
                print("\nDid not receive a response. Retrying Query.....")
                print("Sending packet: ",packet)
                s.sendto(packet.encode(),(HOST,PORT))
        data = s.recv(1024)
        print("Data Received: ", data.decode())
        print("")
        # false if it doesnt rceive
        return True
        # s.close()

#    def peer_discovery_recv(self, connection, address):
#        data = connection.recv(1024)
#        if data == 0:
#            print("connection closed by client")
#        packet = 'ACK'
#        self.s.sendto(packet.encode(), (self.POCNAME,self.POCPORT))
#        if (str(data).find("PEER") == 0):
#            print(data)
#            data = data.decode().split()
#        data = ast.literal_eval(data[5:])
#        for item in data:
#            print('')
            
     def peer_discovery_recv(self, HOSTNAME, PORT, socket):
        self.socket = socket
        self.socket.bind((HOSTNAME, PORT))
        self.socket.listen(5)
        (conn, add) = socket.accept()
        while (conn, add) != null:
            process = multiprocessing.Process(target=self.handle_peers(), args=(conn, add))
            process.start()
            (conn, add) = socket.accept()
        
     def handle_peers(self, sock, add):
        self.sock = sock
        self.add = add
         
        data = sock.recv(1024)
        while data != "":
            if (str(data).find("PEER") == 0):
                print(data)
                data = data.decode().split()
            data = ast.literal_eval(data[5:])
            for (host, port) in data:
                print str(host, port)
                if (host, port) not in knownlist:
                    knownlist.append((host, port))
                    newlist.append((host,port))
            data = sock.recv(1024)
        
        sock.shutdown()
        sock.close()


def peer_discovery(ringo):
    while len(ringo.knownlist) != ringo.n - 1:
        ringo.peer_discovery_send(ringo.pocname, ringo.pocport)
        ringo.peer_discovery_recv(ringo.localhostname, ringo.localport, ringo.socket)

        templist = ringo.newlist[:]
        for host,port in templist:
            ringo.peer_discovery_send(host,port)
        ringo.newlist = list(set(ringo.newlist).difference(set(templist)))


if __name__ == '__main__':
    ringo = Ringo(FLAG, LOCALHOSTNAME, LOCALPORT, POCNAME, POCPORT, N)
    peer_discovery(ringo)
    while True:
        com = input('Ringo Command: ').split()
        # if com[0] == 'offline':
        #   #   TODO
        #   exit(0)
        # elif com[0] == 'send':
        #   #   TODO
        #   # send(FLAG, LOCALPORT, POCNAME, POCPORT)
        # elif com[0] == 'show-matrix':
        #   #   TODO
        # elif com[0] == 'show-ring':
        #   #   TODO
        # elif com[0] == 'disconnect':
        #     # PROB NEED TO CHANGE
        #     exit(0)



# class Server: 
#     def __init__(self, Ringo):
#         self.hostname = Ringo.localhostname
#         self.port = Ringo.localport
#         self.pocport = Ringo.pocport
#         self.pocname = Ringo.pocname
    
#     def start(self): 
#         self.socket = Ringo.s
#         self.socket.bind((self.hostname, self.port))
#         self.socket.listen(5)
#         while True: 
#             conn, add = self.socket.address()
#             process = multiprocessing.Process(target=Ringo.peer_discovery_recv(), args=(conn,add))
#             process.start()
