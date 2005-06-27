#!/usr/bin/env python
"""
#############################################################################################
# Name: SwitchoverDeleter.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-27
#
# Description: First here is a description of a DRBD pair:
#              
#   machine1:/apps/                          machine2:/apps/
#            /backupMachine2/                         /backupMachine1/
#
#   The first thing to know when using this program is the name of the mount point of the 
#   drbd partition. The name 'backupMachine?' is only an example.
#
#   When one member of a DRBD pair crash (machine1 for example), the program SwitchoverCopier.py will be used
#   to copy data from machine2:/backupMachine1/ to machine2:/apps/. The data that will
#   be copied is coming from receivers and senders directories. The job of determining which
#   directories correspond to receivers and senders is done by an appropriate manager (PDS or PX).
# 
#   The files copied will be logged and these logs (one per directory, location: /apps/{px|pds}/switchover)
#   will be used to erase these files on machine1:/apps/
# 
#   Usage:
#
#   SwitchoverDeleter (-s|--system) {PDS | PX}\n"
#
#############################################################################################
"""

from Logger import Logger
import os, pwd, sys, getopt

def usage():
    print "\nUsage:\n"
    print "SwitchoverDeleter (-s|--system) {PDS | PX}\n"
    print "-s, --system: PDS or PX"

class SwitchoverDeleter:

    LOG_LEVEL = "INFO"                   # Logging level
    STANDARD_ROOT = 'test'

    # Make sure that user pds run this program
    if not os.getuid() ==  pwd.getpwnam('pds')[2]:
        pdsUID = pwd.getpwnam("pds")[2]
        os.setuid(pdsUID)

    def __init__(self):

        self.getOptionsParser() 

        if SwitchoverDeleter.SYSTEM == 'PX': 
            from PXManager import PXManager
            manager = PXManager('/apps/px/')
            LOG_NAME = manager.LOG + 'SwitchoverDeleter.log'    # Log's name
            SwitchoverDeleter.SWITCH_DIR = '/apps/px/switchover/'

        elif SwitchoverDeleter.SYSTEM == 'PDS':
            from PDSManager import PDSManager
            manager = PDSManager('/apps/pds/')
            LOG_NAME = manager.LOG + 'SwitchoverDeleter.log'   # Log's name
            SwitchoverDeleter.SWITCH_DIR = '/apps/pds/switchover/'

        self.logger = Logger(LOG_NAME, SwitchoverDeleter.LOG_LEVEL, "Deleter")
        self.logger = self.logger.getLogger()
        manager.setLogger(self.logger)

        self.logger.info("Beginning program SwitchoverDeleter")
        self.manager = manager

    def getDestDir(self, sourceDir, replacement):
        parts = sourceDir.split('/', 2)
        parts[1] = replacement

        return '/'.join(parts)

    def delete(self):
        
        if os.path.isdir(SwitchoverDeleter.SWITCH_DIR):
            files = os.listdir(SwitchoverDeleter.SWITCH_DIR)

            for file in files:
                file = SwitchoverDeleter.SWITCH_DIR + file
                # regular file
                if os.path.isfile(file):
                    self.manager.deleteSwitchoverFiles(file, self.logger)

                    try:
                        os.unlink(file)
                        self.logger.info("Container  %s has been deleted" % file)
                    except:
                        (type, value, tb) = sys.exc_info()
                        self.logger.error("Problem deleting %s (container file), Type: %s Value: %s" % (file, type, value))

    def getOptionsParser(self):
        
        system = False
        try:
            opts, args = getopt.getopt(sys.argv[1:], 's:h', ['help', 'system='])
            #print opts
            #print args
        except getopt.GetoptError:
            # print help information and exit:
            usage()
            sys.exit(2)

        for option, value in opts:
            if option in ('-h', '--help'):
                usage()
                sys.exit()
            if option in ('-s', '--system'):
                system = True
                if value in ['PDS', 'PX']:
                    SwitchoverDeleter.SYSTEM = value
                else:
                    usage()
                    sys.exit(2)

        # We must give a system
        if system is False:  
            usage()
            sys.exit(2)

if __name__ == '__main__':

    deleter =  SwitchoverDeleter()
    deleter.delete()
    deleter.logger.info("Ending program SwitchoverDeleter")
