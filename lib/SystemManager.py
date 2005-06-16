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

    def __init__(self):
        self.logger = None
        self.rxNames = []            # Name is based on filename found in RX_CONF
        self.txNames = []            # Name is based on filename found in TX_CONF
        self.runningRxNames = []     # We only keep the Rx for which we can find a PID
        self.runningTxNames = []     # We only keep the Tx for which we can find a PID 
        self.rxPaths = [] 
        self.txPaths = [] 

    def setLogger(self, logger):
        self.logger = logger

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

    def copyFiles(self, sourceDir, targetDir, logger):
        """
        Copy all files under the given sourceDir(supposed to begin by a /apps2/) to 
        the /apps/... on the same machine
        """
        if os.path.isdir(sourceDir):
            files = os.listdir(sourceDir)
        else:
            print "This is not a directory (%s)" % (sourceDir)
            return

        for file in files:
            try:
                # FIXME
                # If targetDir doesn't exist, does I create it?
                # Should create a file with all the files that are copied
                shutil.copy2(sourceDir + file, targetDir + file)
            except:
                # FIXME: Find the correct exceptions that can arrive here
                print "Problem while shutil.copy2(%s, %s)" % (sourceDir + file, targetDir + file)

    def setFilesToDelete(self, filename):
        """
        Create a list from all the entries in the filename. This list
        will contains all the files we want to delete on /apps/ of the 
        broken machine before it restarts.
        """
        pass

    def deleteFiles(self, files):
        """
        Delete all files from the given list.
        """
        pass

if __name__ == '__main__':
  
    manager = SystemManager()
    print manager.getRxNames()
    print manager.getTxNames()
