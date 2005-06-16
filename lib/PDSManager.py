"""
#############################################################################################
# Name: PDSManager.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-14
#
# Description:
#
#############################################################################################
"""
import os, os.path, commands, re, pickle, time, logging
import SystemManager
from SystemManager import SystemManager

class PDSManager(SystemManager):

    # Maybe all these names should be put in a file PDSPath.py? Not sure, if in fact
    # a PDSManager is a entry point to PDS API!

    # Useful directories
    ROOT = '/apps/pds/'
    BIN = ROOT + 'bin/'
    LOG = ROOT + 'log/'
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'RAW/'
    TXQ = ROOT + 'home/'
    DB = ROOT + 'pdsdb/'
    INFO = ROOT + 'info/'
    RX_CONF = ETC
    TX_CONF = ETC 

    # Useful files
    PROD = "pdschkprod.conf"
    SWITCH = "pdsswitch.conf"
    STARTUP = "PDSstartupinfo"
    TOGGLE = "ToggleSender"
    RESEND = "pdsresend"

    # Useful paths (directory + file)
    FULLPROD = ETC + PROD
    FULLSWITCH = ETC + SWITCH
    FULLSTARTUP = INFO + STARTUP
    FULLTOGGLE = BIN + TOGGLE

    def __init__(self):
        SystemManager.__init__(self)
        self.setRxNames()
        self.setTxNames()
        self.setRxPaths()
        self.setTxPaths()

        #print self.getRxNames()

    def setRunningRxNames(self):
        """
        Set a list of receivers' name. We choose receivers that have a .conf file in RX_CONF
        and we verify that these receivers have a process associated to them.
        """
        pass

    def setRunningTxNames(self):
        """
        Set a list of senders' name. We choose senders that have a .conf file in TX_CONF 
        and we verify that these senders have a process associated to them.
        """
        pass

    def setRxNames(self):
        """
        Set a list of input directories' name. We choose directories that are STARTED in RX_CONF.
        We don't verify if these directories have a process (pdschkprod) associated to them.
        """
        rxNames = []

        prodfile = open (PDSManager.FULLPROD, "r")
        lines = prodfile.readlines()

        for line in lines:
            match = re.compile(r"^in_dir\s+(\S+)").search(line)
            if (match):
                # We skip the RAW/ part
                rxNames.append(match.group(1)[4:])
        self.rxNames = rxNames
        prodfile.close()

    def setTxNames(self):
        """
        Set a list of client's name. We choose clients that are STARTED in TX_CONF.
        We don't verify if these clients have a process associated to them.
        """
        txNames = []

        startup = open(PDSManager.FULLSTARTUP, "r")
        lines = startup.readlines()

        for line in lines:
            if (re.compile(r"pdssender").search(line)):
                match = re.compile(r".* (\d+) (\S+) (\S+) (\d+) info/(\S+) log/(\S+) .*").search(line)
                (pid, name, status, date, config, logfile) =  match.group(1, 2, 3, 4, 5, 6)
                txNames.append(name)
        self.txNames = txNames
        startup.close()

    def setRxPaths(self):
        """
        Set a list of input directories' path. We choose directories that have a .conf file in RX_CONF.
        We don't verify if these directories have a process associated to them.
        """
        rxPaths = []
        for name in self.rxNames:
            rxPaths.append(PDSManager.RXQ + name + '/')
        self.rxPaths = rxPaths

    def setTxPaths(self):
        """
        Set a list of input directories' path. We choose directories that have a .conf file in RX_CONF.
        We don't verify if these directories have a process associated to them.
        """
        txPaths = []
        for name in self.txNames:
            txPaths.append(PDSManager.TXQ + name + '/incoming/')
        self.txPaths = txPaths


if __name__ == '__main__':
  
    manager = PDSManager()
    #print manager.getRxNames()
    #print manager.getTxNames()
    print manager.getRxPaths()
    print manager.getTxPaths()
