"""
#############################################################################################
# Name: SystemManager.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-14
#
# Description: General System Manager. Regroup functionalities common to all managers.
#              PXManager and PDSManager will implement features particular to them.
#
#############################################################################################

"""
import os, os.path, sys, shutil, commands, re, pickle, time, logging

class SystemManagerException(Exception):
    pass

class SystemManager:

    def __init__(self):
        self.logger = None           # self.setLogger will be used by the application using a Manager 
        self.rxNames = []            # Names are based on filenames found in RX_CONF
        self.txNames = []            # Names are based on filenames found in TX_CONF
        self.runningRxNames = []     # We only keep the Rx for which we can find a PID
        self.runningTxNames = []     # We only keep the Tx for which we can find a PID 
        self.rxPaths = []            # Receivers (input directories in PDS parlance) paths
        self.txPaths = []            # Transmitters (clients in PDS parlance, senders in PX parlance) paths

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

    def copyFiles(self, sourceDir, targetDir, copyLog=None):
        """
        Copy all files (no directories) under the given sourceDir(supposed to begin by a /apps2/) to 
        the /apps/... on the same machine
        """
        if os.path.isdir(sourceDir):
            files = os.listdir(sourceDir)
        else:
            print "This is not a directory (%s)" % (sourceDir)
            return

        if not os.path.isdir(targetDir):
            try:
                self.createDir(targetDir)
            except: 
                if self.logger is None:
                    print "Unable to create directory (%s)" % (targetDir)
                else:
                   self.logger.error("Unable to create directory (%s)" % (targetDir))
                return

        if copyLog is not None:
            cpLog = open(copyLog, 'w')

        for file in files:
            
            # We are not interessed in directory
            if os.path.isdir(file):
                continue
            try:
                # FIXME
                # Should create a file with all the files that are copied
                shutil.copy2(sourceDir + file, targetDir + file)
                if copyLog is not None:
                    cpLog.write(targetDir + file + '\n')
            except:
                # FIXME: Find the correct exceptions that can arrive here
                (type, value, tb) = sys.exc_info()
                if self.logger is None:
                    print "Problem while shutil.copy2(%s, %s)" % (sourceDir + file, targetDir + file)
                else:
                    self.logger.error("Problem with shutil.copy2(%s, %s) => Type: %s, Value: %s" % 
                                                     (sourceDir + file, targetDir + file, type, value))
                                                     
        if copyLog is not None:
            cpLog.close()

    def createDir(self, dir):
        if not os.path.isdir(dir):
            os.makedirs(dir, 0755)

    def changePrefixPath(self, path):
        if path[0:7] == '/apps2/':
            path = '/apps/' + path[7:]
            print path
            return path
        else:
            if self.logger is None:
                print "This directory (%s) doesn't begin  by /apps2/" % (path)
                return None
            else:
                self.logger.warning("This directory (%s) doesn't begin  by /apps2/" % (path))
                return None

    def deleteFiles(self, copyLog, deleteLog=None):
        """
        Delete all files listed in the copyLog
        """
        try:
            cpLog = open(copyLog, 'r')
        except:
            (type, value, tb) = sys.exc_info()
            if self.logger is None:
                print "Problem opening %s , Type: %s Value: %s" % (cpLog, type, value)
            else:
               self.logger.error("Problem opening %s , Type: %s Value: %s" % (cpLog, type, value))

        if deleteLog is not None:
            delLog = open(deleteLog, 'w')

        filesToDelete = cpLog.readlines()

        for file in filesToDelete:
            file = file.strip()
            try:
                os.unlink(file)
                if deleteLog is not None:
                    delLog.write(file +  "\n")
            except:
                (type, value, tb) = sys.exc_info()
                if self.logger is None:
                    print "Problem deleting %s , Type: %s Value: %s" % (file, type, value)
                else:
                    self.logger.error("Problem deleting %s , Type: %s Value: %s" % (file, type, value))
                    
        if deleteLog is not None:
            delLog.close()


if __name__ == '__main__':
  
    manager = SystemManager()
    #print manager.getRxNames()
    #print manager.getTxNames()
    #manager.createDir('/apps/px/tutu/')
    #manager.createDir('/apps/px/tata/')
    manager.changePrefixPath('/apps/px/toto/')
    manager.changePrefixPath('/apps/px/tutu/')
    manager.copyFiles('/apps/px/toto/', '/apps/px/tarteau/', '/apps/px/tarteau/copy.log')
    manager.deleteFiles('/apps/px/tarteau/copy.log', '/apps/px/tarteau/delete.log')

