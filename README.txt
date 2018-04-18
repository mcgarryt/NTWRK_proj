Marcus Loo - mloo3@gatech.edu
Nick Mcgarry - nmcgarry3@gatech.edu
4/17/18
PA2 Milestone 3

 
--pa2/
	| --ringo.py - the actual ringo itself that can be ran
	| --README.txt - this file that descripts everything
	| --sample.txt - sample output
	| --Design Report Final.pdf - design of the entire project

This was ran and tested using python3 on the networklab1,2,3
It follows the expected command of:
ringo <flag> <local-port> <PoC-name> <PoC-port> <N>
An example is:
python3 ringo.py flag 49100 networklab2.cc.gatech.edu 49101 3.


Milestone 3: Input sanitation was handled in a basic manner: if the incorrect number of inputs are given, then it throws an error and exits gracefully. For Ringos with a null PoC, we have described that behavior with commands such as "python3 ringo.py F 49100 0.0.0.0 0 3", where the PoC port and host names have been functionally annulled. If there is a true null PoC declaration, i.e., "python3 ringo.py F 3", then we throw an error. It is unknown whether this is intentional behavior. Furthermore, because of the way we threaded our program, there are an excess of print statements left in debugging--we print many things at once on each Ringo. We considered many edge cases in our programming, but due to time constraints, we were unable to fully test every possible edge case, so there may be bugs not listed here. Furthermore, if a Ringo goes offline during data transfer, we do not go the other available way, at least we don't think we do.
Sometimes, the Ringo Command text doesn't show up, but it is able to handle command inputs. Sometimes, it also shows up too many times. 
Because of feedback on Milestone 2, we fixed our Peer Discovery methods to allow for situations where the first Ringo has a null PoC, and also allows for situations where the first Ringo has a null PoC and all of the other Ringos in the network are connected to that one as their initial PoC--we get full discovery in all cases now.



# REFERENCE WEBSITES
## THREADING AND SOCKETING
# https://gist.github.com/micktwomey/606178
# https://eli.thegreenplace.net/2011/05/18/code-sample-socket-client-thread-in-python
# https://docs.python.org/3/howto/sockets.html
# https://stackoverflow.com/questions/1894269/convert-string-representation-of-list-to-list-in-python
# https://gist.github.com/arthurafarias/7258a2b83433dfda013f1954aaecd50a
# https://github.com/phvargas/TSP-python/blob/master/TSP.py