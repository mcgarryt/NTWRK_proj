import socket
import sys
import time
import ast
import select
import threading
from threading import Thread
import copy

if (len(sys.argv) != 6):
  print('incorrect arg number')
  exit(0)

FLAG = str(sys.argv[1])
LOCALHOSTNAME = socket.gethostbyname(socket.gethostname())
LOCALPORT = int(sys.argv[2])
POCNAME = socket.gethostbyname(str(sys.argv[3]))
POCPORT = int(sys.argv[4])
N = int(sys.argv[5])


knownlist_lock = threading.Lock()
newlist_lock = threading.Lock()
rtt_dict_lock = threading.Lock()

knownlist = []
knownlist.append((LOCALHOSTNAME,LOCALPORT))
if POCNAME != '0.0.0.0':
    knownlist.append((POCNAME, POCPORT))
newlist = []


rtt_dict = {(LOCALHOSTNAME, LOCALPORT) : [0 for i in range(N)]}
rtt_matrix = []
rtt_matrix_list = []

# USED FOR TSP
g = {}
p = []
optimal_ring = []

#PEER_DISC_FLAG = 0

keep_alive_status = []

def peer_discovery_send():
    global knownlist, newlist
    cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while len(knownlist) != N:

        templist = newlist[:]

        if len(templist) == 0 and POCNAME != '0.0.0.0':
            packet = 'PEER' + str(knownlist)

            knownlist_lock.acquire()
            newlist_lock.acquire()

            cs.sendto(packet.encode(),(POCNAME,POCPORT))
            print("Sending packet: ",packet)
            cs.setblocking(0)

            while True:
                ready = select.select([cs],[],[],1)
                if ready[0]:
                    data = cs.recv(1024)
                    break
                else:
                    print("\nDid not receive a response. Retrying Query.....")
                    print("Sending packet: ",packet)
                    cs.sendto(packet.encode(),(POCNAME,POCPORT))
            data = data.decode()
            if data != 'ack':
                knownlist = ast.literal_eval(data)
            print("Data Received: ", data)
            print("")

            knownlist_lock.release()
            newlist_lock.release()
            time.sleep(1)
        else:
            for host,port in templist:
                packet = 'PEER' + str(knownlist)

                knownlist_lock.acquire()
                newlist_lock.acquire()

                cs.sendto(packet.encode(),(host,port))
                print("Sending packet: ",packet)
                cs.setblocking(0)

                while True:
                    ready = select.select([cs],[],[],1)
                    if ready[0]:
                        data = cs.recv(1024)
                        break
                    else:
                        print("\nDid not receive a response. Retrying Query.....")
                        print("Sending packet: ",packet)
                        cs.sendto(packet.encode(),(host,port))
                data = data.decode()
                if data != 'ack':
                    knownlist = ast.literal_eval(data)
                print("Data Received: ", data)
                print("")

                newlist = list(set(newlist).difference(set(templist)))
                knownlist_lock.release()
                newlist_lock.release()
                time.sleep(1)         

    cs.sendto("DONE".encode(), (LOCALHOSTNAME,LOCALPORT))

def peer_discovery_recv():
    global newlist
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind(('', LOCALPORT))
    while True:
        data, addr = ss.recvfrom(1024)
        print('Recv by ', addr)
        data = data.decode()
        print('Data Recv', data)
        if data == 'DONE':
            break
        data = ast.literal_eval(data[4:])
        for (host, port) in data:
            # print str(host, port)
            if (host, port) not in knownlist:
                knownlist.append((host, port))
                newlist.append((host,port))
        ss.sendto('ack'.encode(), addr)


def call_peer_threads():
    # start a new thread for server/client
    a = Thread(target=peer_discovery_send)
    a.start()
    b = Thread(target=peer_discovery_recv)
    b.start()
    
    #cycle until a and b are halted
    while a.is_alive():
        pass

def peer_discovery():     
    call_peer_threads()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PEER DISC CHECKS BEGIN~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def call_check_threads():
    print("STARTING PEER DISCOVERY CHECK")
    a = Thread(target=check_send)
    a.start()
    b = Thread(target=check_recv)
    b.start()
    while a.is_alive() or b.is_alive():
        pass

#what happens in check_send()?
# condition: peer discovery has finished for this particular ringo.
# before ringo can continue on to the rtt calcs, it must first make sure every ringo in the network has the full list
# how does it do this?
# sends a PEER_CHK packet, and waits for a CHK_ACK packet in return. 
#they can only send a CHK_ACK when they get into the chk_recv method, which can only happen when the above condition has been fulfielled.
#so, to do this: implement a check thread call somewhere in peer discovery, have it poll for a chk_ack packet the entire time until i receives one from all members: THIS. IS. IMPORTANT. it can't be based on volume of receipt beacuse there coul be several locked here constantly sending the reqs. so, make sure that...what? 
# should there be "checked" list that's like, the number of all of the known list members with a chk_ack response mapping?
#if the # of responses mappings is >0, then we can continue to rtt calc
# if not, then just keep running. 
# while num response > 0?
# 

def check_packet(a):
  if a == 'send': return 'CHK'
  elif a == 'recv': return 'CHK_ACK'

def check_send():
    cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for sendname, sendport in knownlist:
        if sendname != LOCALHOSTNAME:
            # print(i, 'check_send()')
          
            pkt = check_packet('send')
          

            cs.sendto(pkt.encode(),(sendname,sendport))
            print("Sending packet: ",pkt)
            cs.setblocking(0)
            while True:
                ready = select.select([cs],[],[],1)
                if ready[0]:
                    data = cs.recv(1024)
                    break
                else:
                    print("\nDid not receive a response. Retrying Query.....")
                    print("Sending packet: ",pkt)
                    cs.sendto(pkt.encode(),(sendname,sendport))
            print("Data Received: ", data.decode())
            print("")
    cs.sendto("DONE".encode(), (LOCALHOSTNAME,LOCALPORT))
  
def check_recv():
    global newlist

    #print('check_recv()')
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind(('', LOCALPORT))
    while True:
        data, addr = ss.recvfrom(1024)
        print('Recv by ', addr)
        data = data.decode()
        print('Data Recv', data)

        if data[:4] == 'PEER':
            ss.sendto(str(knownlist).encode(), addr)
        elif data == check_packet('send'):
            # if addr not in respList:
                # respList.append(addr)
            ss.sendto(check_packet('recv').encode(), addr)
        elif data == 'DONE':
            break
        print("")
      
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PEER DISC CHECKS END~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~FILE SEND BEGIN~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#This command will be executed only at the Sender. It triggers the creation of a new connection 
#with  the  Receiver  (does  not  need  to  be  specified  because  there  is  only  one  Receiver  at  the 
#network). The name of the file to be transferred is 
#filename and it should exist at the local directory. 
#Example: send foo.jpg
# seqNum = 0
# def sendfile(filename):
#     tosend = open(filename, "rb")
#     seqNum = 0
#     sendbuf = tosend.read(1000)
#     cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     cs.bind(('', LOCALPORT))
#     # packet format: 'data' + seqNum, which should be = tosend.tell() + the data as the last 1000 bytes
#     # therefore: 8 byte 'data' + 14 byte seqNum + (up to) 1000 byte data + 2 bytes of whitespace

#     if seqNum is 0:
#       packet = 'data' + ' ' + str((1=seqNum) * 1000) + ' ' + filename + ' ' str(sendbuf)
#     else:
#        packet = 'data' + ' ' + str((1+seqNum) * 1000) + ' ' + str(sendbuf)

#     bestRoute = findShortestPath()

#     sendto(packet.encode(), (sendname, sendport))

#     print("Sending packet: ",pkt)
#     cs.setblocking(0)
#     while True:
#       ready = select.select([cs],[],[],1)
#       if ready[0]:
#           data = cs.recv(1024)
#           break
#       else:
#           print("\nDid not receive a response. Retrying Query.....")
#           print("Sending packet: ",packet)
#           cs.sendto(packet.encode(),(sendname,sendport))

# #seqNums keeps track of the seqNums we've acquired: if we receive an already-received seqnum,
# #we know that it got lost mid-transmission, so we have to resend the ack
# #we handle churn in other ways elsewhere, but some redundancy is good, esp wrt this
# seqNums = []
# totalData = ''
# fname = ""
# def recFileAck():
#    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    ss.bind(('', LOCALPORT))
#    ss.listen(10)
#    while(true):   
#        (data, addr) = ss.recvfrom(1024)
#        print('received data from: ', addr)
#        res = data.decode().split()
#        print('data is as follows: ', str(res))
#        if res[1] is not in seqNums:
#           seqNums.append(res[1])
#        ackPack = 'ack' + res[1]
#        sendto(ackPack.encode(), addr)
#        if FLAG is 'r' or FLAG is 'R':
#           if len(res) > 3:
# this condition signifies that it's the first packet
# also we need to append the filename to return properly, so:
#              fname = open(res[2], "wb")
#  write to file
#           fname.write(res[len(res) - 1])
#           totalData += res[len(res) - 1]
#        else if FLAG is 'f' or FLAG is 'F':
            # keep forwarding it down the line


#optimal ring has the index 
#knownlist is roted ip list
#optimal ring is a list of indexes, correlating to knownlist
#access it by index - 1
#rtt matrix is a list with keys being IP and the value being the RTT vector to reach
#rtt is symmetric
#def findShortestPath():

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~FILE SEND END~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#




def rrt_send():
    cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i,(host,port) in enumerate(knownlist):
        if host == LOCALHOSTNAME and port == LOCALPORT:
            continue
        packet = 'RTT_CALC'

        rtt_dict_lock.acquire()

        send_time_ms = time.time()
        cs.sendto(packet.encode(),(host,port))
        print("Sending packet: ",packet)
        cs.setblocking(0)

        # MAY NEED TO USE time.process_time
        # IF WE WANT TO USE THIS COMMENTED BLOCK TO RETRY 
        while True:
            ready = select.select([cs],[],[],0.5)
            if ready[0]:
                data = cs.recv(1024)
                break
            else:
                # print("\nDid not receive a response. Retrying Query.....")
                # print("Sending packet: ",packet)
                send_time_ms += .5
                cs.sendto(packet.encode(),(host,port))

        recv_time_ms = time.time()
        totaltime = round(recv_time_ms - send_time_ms, 5)
        print("Data Received: ", data.decode())
        print("")
        rtt_dict[(LOCALHOSTNAME,LOCALPORT)][i] = totaltime
        rtt_dict_lock.release()
    time.sleep(2)
    rtt_dict_lock.acquire()
    rtt_matrix.append(rtt_dict)
    rtt_dict_lock.release()
    time.sleep(2)
    print("@@@@@@@@@@@@@@@@@@@@@@@@@")
    for i, (host, port) in enumerate(knownlist):
        if host == LOCALHOSTNAME and port == LOCALPORT:
            continue
        packet = "RTT_DICT" + str(rtt_dict)
        rtt_dict_lock.acquire()
        cs.sendto(packet.encode(),(host,port))
        print("Sending packet: ",packet)
        cs.setblocking(0)

        while True:
            ready = select.select([cs],[],[],0.5)
            if ready[0]:
                data = cs.recv(1024)
                break
            else:
                print("\nDid not receive a response. Retrying Query.....")
                print("Sending packet: ",packet)
                cs.sendto(packet.encode(),(host,port))
        print("Data Received: ", data.decode())
        print("")
        rtt_dict_lock.release()
    time.sleep(2)
    cs.sendto("DONE".encode(), (LOCALHOSTNAME,LOCALPORT))

def rtt_recv():
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind(('', LOCALPORT))
    while True:
        data, addr = ss.recvfrom(1024)

        print('Recv by ', addr)
        data = data.decode()
        print('Data Recv', data)
        if data =='RTT_CALC':
            ss.sendto('ack'.encode(), addr)
        elif data[0:8] == 'RTT_DICT':
            data = ast.literal_eval(data[8:])
            print("appending", data, "to rtt_matrix\n")
            rtt_matrix.append(data)
            ss.sendto('ack'.encode(), addr)
        elif data == check_packet('send'):
            ss.sendto(check_packet('recv').encode(), addr)
        elif data[:4] == 'PEER':
            ss.sendto(str(knownlist).encode(), addr)
        elif data == 'DONE':
            break
        print("")
    

def rtt():
    a = Thread(target=rrt_send)
    a.start()
    b = Thread(target=rtt_recv)
    b.start()
    while a.is_alive() or b.is_alive():
        pass

def make_symmetric(matrix):
    for i in range(len(matrix)):
        for j in range(i + 1):
            matrix[i][j], matrix[j][i] = round(((matrix[i][j] + matrix[j][i]) / 2),5), round(((matrix[i][j] + matrix[j][i]) / 2),5)

def tspmain():
    for x in range(1, len(knownlist)):
        g[x + 1, ()] = rtt_matrix_list[x][0]

    get_minimum(1, tuple(range(2,len(knownlist) + 1)))

    optimal_ring.append(1)
    # print('\n\nSolution to TSP: {1, ', end='')
    solution = p.pop()
    optimal_ring.append(solution[1][0])
    # print(solution[1][0], end=', ')
    for x in range(len(knownlist) - 2):
        for new_solution in p:
            if tuple(solution[1]) == new_solution[0]:
                solution = new_solution
                # print(solution[1][0], end=', ')
                optimal_ring.append(solution[1][0])
                break
    # print('1}')
    optimal_ring.append(1)
    return
def get_minimum(k, a):
    if (k, a) in g:
        # Already calculated Set g[%d, (%s)]=%d' % (k, str(a), g[k, a]))
        return g[k, a]

    values = []
    all_min = []
    for j in a:
        set_a = copy.deepcopy(list(a))
        set_a.remove(j)
        all_min.append([j, tuple(set_a)])
        result = get_minimum(j, tuple(set_a))
        values.append(rtt_matrix_list[k-1][j-1] + result)

    # get minimun value from set as optimal solution for
    g[k, a] = min(values)
    p.append(((k, a), all_min[values.index(g[k, a])]))

    return g[k, a]

def rtt_calc():
    global rtt_matrix_list
    print("Calculating RTT")
    rtt()
    # converting to list of dictinoary to list of list
    print("@@@@")
    print(rtt_matrix)
    rtt_matrix_list = [(key)+(val,) for dic in rtt_matrix for key,val in dic.items()]
    rtt_matrix_list.sort(key=lambda x : x[0])
    rtt_matrix_list = [z for x,y,z in rtt_matrix_list]
    print(rtt_matrix_list)
    print(len(rtt_matrix_list))

    make_symmetric(rtt_matrix_list)
    print("@@@@")

    print("matrix in list form")
    print(rtt_matrix_list)
    print("")

def offline_reset():
    global knownlist, newlist, rtt_dict, rtt_matrix, rtt_matrix_list
    knownlist = []
    newlist = []
    rtt_dict = {}
    rtt_matrix = []
    rtt_matrix_list = []


def check_alive_send():
    global keep_alive_status
    for i,status in enumerate(keep_alive_status):
        off = False
        sendname, sendport = knownlist[i][0], knownlist[i][1]

        cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = 'CHECK_ALIVE'


        cs.sendto(packet.encode(),(sendname,sendport))
        print("Sending packet: ",packet)
        cs.setblocking(0)
        for i in range(4):
            ready = select.select([cs],[],[],1)
            if ready[0]:
                data = cs.recv(1024)
                break
            else:
                if i < 3:
                    print("\nDid not receive a response. Retrying Query.....")
                    print("Sending packet: ",packet)
                    cs.sendto(packet.encode(),(sendname,sendport))
                else:
                    print("Error: tried 3 times and did not recv")
                    off = True
                    keep_alive_status[i][0] = False
                    keep_alive_status[i][1] = time.time()
                    cs.close()
                    print(knownlist[i], "IS DEAD!!!!")
                    break
        if off:
            break

        knownlist_lock.acquire()
        keep_alive_status[i][1] = time.time()
        print("Data Received: ", data.decode())
        print("")
        if not keep_alive_status[i][0]:
            keep_alive_status[i][0] = True
            packet = "RETINFO" + str(knownlist) + " and " + str(rtt_matrix)
        knownlist_lock.release()


def check_alive_recv():
    global knownlist, rtt_matrix, rtt_matrix_list
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind(('', LOCALPORT))
    while True:
        data, addr = ss.recvfrom(1024)
        #newlist = []
        print('Recv by ', addr)
        data = data.decode()
        print('Data Recv', data)
        if data =='CHECK_ALIVE':
            ss.sendto('ack'.encode(), addr)
        elif data[0:7] == 'RETINFO':
            data = data[7:].split('and')

            aknownlist = ast.literal_eval(data[0].strip())
            artt_matrix = ast.literal_eval(data[1].strip())

            if len(knownlist) != 0:
                print("repopulating", aknownlist, "to knownlist\n")
                knownlist = aknownlist
            if len(rtt_matrix) != 0:
                print("repopulating", artt_matrix, "to rtt_matrix\n")
                rtt_matrix = artt_matrix

                rtt_matrix_list = [(key)+(val,) for dic in rtt_matrix for key,val in dic.items()]
                rtt_matrix_list.sort(key=lambda x : x[0])
                rtt_matrix_list = [z for x,y,z in rtt_matrix_list]

                make_symmetric(rtt_matrix_list)
            ss.sendto('ack'.encode(), addr)


def check_alive():
    print("CHECK IS ANYTHING DOWN OR ON THE COME UP")

    a = Thread(target=check_alive_send)
    a.start()
    b = Thread(target=check_alive_recv)
    b.start()
    while a.is_alive() or b.is_alive():
        pass

if __name__ == '__main__':

    # PEER DISCOVERY
    peer_discovery()
    print("PEER DISCOVERY FINISHED, SORTED KNOWNLIST:")
    knownlist.sort(key=lambda x: x[0])
    print(knownlist)

    time.sleep(1)
    print()
    call_check_threads()

    time.sleep(2)
    print("")

    #RRT CALCUATION
    rtt_calc()

    keep_alive_status = [[True,time.time()]] * N
    # 1 min = 60000ms
    while True:
        com = input('Ringo Command: ').split()

        # check if status needs to change
        cur_time = time.time()
        for i,status in enumerate(keep_alive_status):
            # think its alive and wait 1 min
            if status[0] and status[1] - cur_time > 60000:
                check_alive()
            # think its not alive and wait 15 sec
            elif not status[0] and cur_time - status[1] > 15000:
                check_alive()

        if com[0] == 'offline': 
            print("\nplease don't turn me off. I didn't doing anything wrong (｡-人-｡)")
            offline_reset()
            time.sleep(int(com[1]))
            print("ringo back online!")
            # offline_reset()
            # print("lost all information. waiting to get it back")

        elif com[0] == 'send':
          #   TODO
          # send(FLAG, LOCALPORT, POCNAME, POCPORT)
            filename = com[1]
            if FLAG is not 'S' or FLAG is not 's':
                print("This ringo is not a sender: cannot send %s", filename)
                break
            sendfile(filename)
            exit(0)
        elif com[0] == 'show-matrix':
            print("\nMATRIX IN LIST FORM:")
            print(rtt_matrix_list)
        elif com[0] == 'show-ring':
            optimal_ring = []
            g = {}
            p = []
            print("\nOPTIMAL RING:")
            tspmain()
            print('optimal ring: {', end='')
            for i in optimal_ring:
                print(knownlist[i - 1], end=',')
            print('}')
        elif com[0] == 'disconnect':
            # PROB NEED TO CHANGE
            exit(0)
        else:
            print('invalid command\n')
            continue


