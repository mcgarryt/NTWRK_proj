import socket
import sys
import time
import ast
import select
import threading
from threading import Thread
import copy

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
knownlist.append((POCNAME, POCPORT))
newlist = []


rtt_dict = {(LOCALHOSTNAME, LOCALPORT) : [0 for i in range(N)]}
rtt_matrix = []
rtt_matrix_list = []

# USED FOR TSP
g = {}
p = []
optimal_ring = []

PEER_DISC_FLAG = 0

def peer_discovery_send(sendname, sendport):
    if sendname and sendport:
        cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = 'PEER' + str(knownlist)

        knownlist_lock.acquire()
        newlist_lock.acquire()

        cs.sendto(packet.encode(),(sendname,sendport))
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
                cs.sendto(packet.encode(),(sendname,sendport))
        print("Data Received: ", data.decode())
        print("")

        knownlist_lock.release()
        newlist_lock.release()

    # false if it doesnt rceive
    # return True
    # s.close()
        
def peer_discovery_recv():
    global newlist
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind(('', LOCALPORT))
    while True:
        data, addr = ss.recvfrom(1024)
        #newlist = []
        print('Recv by ', addr)
        data = data.decode()
        print('Data Recv', data)
        data = ast.literal_eval(data[4:])
        for (host, port) in data:
            # print str(host, port)
            if (host, port) not in knownlist:
                knownlist.append((host, port))
                newlist.append((host,port))
        ss.sendto('ack'.encode(), addr)

        
        break


def call_peer_threads(sendname, sendport):
    # start a new thread for server/client
    a = Thread(target=peer_discovery_send,args=(sendname, sendport))
    a.start()
    b = Thread(target=peer_discovery_recv)
    b.start()
    
    #cycle until a and b are halted
    while a.is_alive() or b.is_alive():
        pass

def peer_discovery():
    global newlist
    call_peer_threads(POCNAME, POCPORT)
    while len(knownlist) != N:
        templist = newlist[:]
        for host,port in templist:
            call_peer_threads(host, port)
        newlist = list(set(newlist).difference(set(templist)))
        # time.sleep(1)

    PEER_DISC_FLAG = 1;



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
    while True and PEER_DISC_FLAG == 1:
        data, addr = ss.recvfrom(1024)
        #newlist = []
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
        elif data == 'DONE':
            break
        elif data[0:4] == 'PEER':
            # while len(knownlist) != N:
            # templist = newlist[:]
            # for host,port in templist:
            #     call_peer_threads(host, port)
            # newlist = list(set(newlist).difference(set(templist)))
            PEER_DISC_FLAG = 0;

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
    rtt_matrix_list = [(key)+(val,) for dic in rtt_matrix for key,val in dic.items()]
    rtt_matrix_list.sort(key=lambda x : x[0])
    rtt_matrix_list = [z for x,y,z in rtt_matrix_list]

    make_symmetric(rtt_matrix_list)

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

if __name__ == '__main__':

    # PEER DISCOVERY
    peer_discovery()
    print("PEER DISCOVERY FINISHED, SORTED KNOWNLIST:")
    knownlist.sort(key=lambda x: x[0])
    print(knownlist)
    time.sleep(3)
    print("")

    #RRT CALCUATION
    rtt_calc()

    keep_alive_status = [(True,time.time())] * N

    while True:
        com = input('Ringo Command: ').split()
        if com[0] == 'offline':
            time.sleep(int(com[1]))
            print("ringo back online!")
            # offline_reset()
            # print("lost all information. waiting to get it back")

        elif com[0] == 'send':
          #   TODO
          # send(FLAG, LOCALPORT, POCNAME, POCPORT)
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


