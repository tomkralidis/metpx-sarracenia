"""
#############################################################################################
# Name: PXManager.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-14
#
# Description:
#
#############################################################################################

"""
import os, os.path, commands, re, pickle, time, logging, fnmatch
import SystemManager
from SystemManager import SystemManager

class PXManager(SystemManager):
# Maybe all these names should be put in a file PXPath.py? Not sure, if in fact
# a PXManager is a entry point to PX API!

    ROOT = '/apps/px/'
    #BIN = ROOT + 'bin/'
    #LIB = ROOT + 'lib/'
    #LOG = ROOT + 'log/'
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'rxq/'
    TXQ = ROOT + 'txq/'
    DB = ROOT + 'db/'
    RX_CONF = ETC + 'rx/'
    TX_CONF = ETC + 'tx/'

    def __init__(self):
        self.setRxNames()           
        self.setTxNames()
        self.setRxPaths()
        self.setTxPaths()

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
        Set a list of receivers' name. We choose receivers that have a .conf file in RX_CONF.
        We don't verify if these receivers have a process associated to them.
        """
        rxNames = []
        for file in os.listdir(PXManager.RX_CONF):
            if file[-5:] != '.conf':
                continue
            else:
                rxNames.append(file[:-5])
        self.rxNames = rxNames
                
    def setTxNames(self):
        """
        Set a list of senders' name. We choose senders that have a .conf file in TX_CONF.
        We don't verify if these senders have a process associated to them.
        """
        txNames = []
        for file in os.listdir(PXManager.TX_CONF):
            if file[-5:] != '.conf':
                continue
            else:
                txNames.append(file[:-5])
        self.txNames = txNames

    def setRxPaths(self):
        """
        Set a list of receivers' path. We choose receivers that have a .conf file in RX_CONF.
        We don't verify if these receivers have a process associated to them.
        """
        rxPaths = []
        for name in self.rxNames:
            rxPaths.append(PXManager.RXQ + name + '/')
        self.rxPaths = rxPaths

    def setTxPaths(self):
        """
        Set a list of clients' path. We choose clients that have a .conf file in TX_CONF.
        We don't verify if these clients have a process associated to them.
        """
        txPaths = []
        txPathsPri = []
        txPathsPriDate = []
        priorities = [str(x) for x in range(1,10)]

        for name in self.txNames:
            txPaths.append(PXManager.TXQ + name + '/')

        for path in txPaths:
            for priority in [pri for pri in os.listdir(path) if pri in priorities]: 
                if os.path.isdir(path + priority):
                    txPathsPri.append(path + priority + '/')

        for path in txPathsPri:
            for date in fnmatch.filter(os.listdir(path), '20[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'):
                if os.path.isdir(path + date):
                    txPathsPriDate.append(path + date + '/')

        #print txPathsPri
        #print txPathsPriDate

        self.txPaths = txPathsPriDate

if __name__ == '__main__':
  
    manager = PXManager()
    #print manager.getRxNames()
    #print manager.getTxNames()
    print manager.getRxPaths()
    print manager.getTxPaths()
