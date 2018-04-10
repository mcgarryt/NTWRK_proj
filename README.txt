Marcus Loo - mloo3@gatech.edu
Nick Mcgarry - nmcgarry3@gatech.edu
3/16/17
PA2

 
--pa2/
	| --ringo.py - the actual ringo itself that can be ran
	| --README.txt - this file that descripts everything
	| --sample.txt - sample output
	| --cs 3251 - Design Report.pdf - design of the entire project

This was ran and tested using python3 on the networklab1,2,3
It follows the expected command of:
ringo <flag> <local-port> <PoC-name> <PoC-port> <N>
An example is:
python3 ringo.py flag 49100 networklab2.cc.gatech.edu 49101 3.
Flag is not implemented yet because that is not needed for peer discovery, rrt, or optimal ring formation.

Currently, input has to be correct or an error will be thrown. Also, this current implementation does not handle any cases that was outside of basic peer discovery, rrt, or optimal ring formation. This means that we assume no ringo turns off, and ringos have at least 1 POC that will not be off during POC. Also the packet and header size wasn't that big of a concern for us in this implementation since data transwer is not in this milestoneThrough early testing of peer discovery I had encountered a bug, but have not been able to replicate it/may have unintentionally fixed it. The only ringo commands that actually work are show-matrix and show-ring. Everything else just calls exit (lol).


# REFERENCE WEBSITES
## THREADING AND SOCKETING
# https://gist.github.com/micktwomey/606178
# https://eli.thegreenplace.net/2011/05/18/code-sample-socket-client-thread-in-python
# https://docs.python.org/3/howto/sockets.html
# https://stackoverflow.com/questions/1894269/convert-string-representation-of-list-to-list-in-python
# https://gist.github.com/arthurafarias/7258a2b83433dfda013f1954aaecd50a
# https://github.com/phvargas/TSP-python/blob/master/TSP.py