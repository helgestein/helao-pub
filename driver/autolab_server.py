#this is the server
import sys
sys.path.append(r"./config")
sys.path.append(r"./driver")
from autolab_driver import Autolab
import mischbares_small
a = Autolab(mischbares_small.config['autolab'])
