# http-rawserver
Http serving application - uses basic python socket library and python select module to emulate threading.

Usage
-----
Program takes http port and filesystem root as command-line arguments. The following serves the contents of project/www on port 80:

    python3 jewel.py 80 ~/project/www
