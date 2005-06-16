"""
#############################################################################################
# Name: SystemManager.py
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


class SystemManagerException(Exception):
    pass

class SystemManager:

    # Maybe all these names should be put in a file PXPath.py? Not sure, if in fact
    # a PXManager is a entry point to PX API!
    ROOT = '/apps/px/'
    BIN = ROOT + 'bin/'
    ETC = ROOT+ 'etc/'
    LIB = ROOT + 'lib/'
    LOG = ROOT + 'log/'
    RXQ = ROOT + 'rxq/'
    TXQ = ROOT + 'txq/'
    DB = ROOT + 'db/'
    RX_CONF = ETC + 'rx/'
    TX_CONF = ETC + 'tx/'

    def __init__(self):
        self.rxNames = []            # Name is based on filename found in RX_CONF
        self.txNames = []            # Name is based on filename found in TX_CONF
        self.runningRxNames = []     # We only keep the Rx for which we can find a PID
        self.runningTxNames = []     # We only keep the Tx for which we can find a PID 
        self.rxPaths = [] 
        self.txPaths = [] 

    def getRunningRxNames(self):
        return self.runningRxNames
    def setRunningRxNames(self):
        """
        Set a list of receivers' name. We choose receivers that have a .conf file in RX_CONF
        and we verify that these receivers have a process associated to them.
        """
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')

    def getRunningTxNames(self):
        return self.runningTxNames
    def setRunningTxNames(self):
        """
        Set a list of senders' name. We choose senders that have a .conf file in TX_CONF 
        and we verify that these senders have a process associated to them.
        """
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')

    def getRxNames(self):
        return self.rxNames

    def setRxNames(self):
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')
                
    def getTxNames(self):
        return self.txNames

    def setTxNames(self):
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')

    def getRxPaths(self):
        return self.rxPaths

    def setRxPaths(self):
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')
                
    def getTxPaths(self):
        return self.txPaths

    def setTxPaths(self):
        raise SystemManagerException('Abstract method: not implemented in SystemManager Class')

if __name__ == '__main__':
  
    manager = SystemManager()
    print manager.getRxNames()
    print manager.getTxNames()
