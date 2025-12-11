# TPRG-2131-PROJECT-2
edit: *files are ready for marking*

Repository containing the files and documentation associated with TPRG 2131 project 2.

Project comprises a complementary pair of scripts, a Server and client. The server periodically measures and transmits VCgen command data from the RPi to the client script.
This automatic process runs 50 times before the server script terminates the session. 

The client side script can be run from either a PC or RPi, displaying the VCgen values within a Graphical User Interface. It features a unicode "LED" indicator to show the connection being established.

The FreeSimpleGUI library is used to build the application window in a simple way, without the heavy financial burden associated with competing Simple GUI Libraries(presumably). 


