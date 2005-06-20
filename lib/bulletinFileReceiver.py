#! /usr/bin/env python2
# -*- coding: UTF-8 -*-
"""
#############################################################################################
# Name: ncsRenamer
# Author: Daniel Lemay (99% of the code is from LPT)
# Date: December 2004
#
# Description: Reads bulletins from disk, compose a valid name, write them to disk and
#              erase the originals. We had to do this this way if we want to use the
#              existing API.
#############################################################################################

 2005/02 PSilva
        thwacked into a lib to convert to 'options' method for
"""
import sys, os, os.path, signal, time
sys.path.insert(1,sys.path[0] + '/../lib')
sys.path.insert(1,sys.path[0] + '/../lib/importedLibs')

import gateway, log, bulletinManager
from DiskReader import DiskReader
import fet

def run(logger, igniter):
    bullManager = bulletinManager.bulletinManager(
         fet.FET_DATA + fet.FET_RX + fet.options.source, logger,
         fet.FET_DATA + fet.FET_RX + fet.options.source,
         '/apps/pds/RAW/-PRIORITY',
         9999,
         '\n',
         fet.options.extension,
         fet.FET_ETC + 'header2client.conf',
         fet.options.mapEnteteDelai,
         fet.options.use_pds )

    while True:
        # If a SIGHUP signal is received ...
        if igniter.reloadMode == True: 
            fet.startup(igniter.options, igniter.logger)
            bullManager = bulletinManager.bulletinManager(
                               fet.FET_DATA + fet.FET_RX + fet.options.source, logger,
                               fet.FET_DATA + fet.FET_RX + fet.options.source,
                               '/apps/pds/RAW/-PRIORITY',
                               9999,
                               '\n',
                               fet.options.extension,
                               fet.FET_ETC + 'header2client.conf',
                               fet.options.mapEnteteDelai,
                               fet.options.use_pds )
            logger.writeLog(logger.INFO, "%s has been reload" % igniter.direction)
            igniter.reloadMode = False

    # We put the bulletins (read from disk) in a dict (key = absolute filename)
        #bulletinsBrutsDict = bullManager.readBulletinFromDisk([bullManager.pathSource])
        reader = DiskReader(bullManager.pathSource, fet.options.batch, False, 4, False, logger)
        reader.sort()
        data = reader.getFilesContent(reader.batch)

        if len(data) == 0:
            time.sleep(1)
            continue

        """
        # Write (and name correctly) the bulletins to disk, erase them after
        for key in bulletinsBrutsDict.keys():
            nb_bytes = len(bulletinsBrutsDict[key])
            logger.writeLog(logger.DEBUG, "Lecture de %s: %d bytes" % (key, nb_bytes))
            bullManager.writeBulletinToDisk(bulletinsBrutsDict[key], True, True)
            os.unlink(key) # erase the file
        """

        for index in range(len(data)):
            nb_bytes = len(data[index])
            logger.writeLog(logger.DEBUG, "Lecture de %s: %d bytes" % (reader.sortedFiles[index], nb_bytes))
            bullManager.writeBulletinToDisk(data[index], True, True)
            try:
                os.unlink(reader.sortedFiles[index])
                logger.writeLog(logger.DEBUG,"%s has been erased", os.path.basename(reader.sortedFiles[index]))
            except OSError, e:
                (type, value, tb) = sys.exc_info()
                logger.writeLog(logger.ERROR, "Unable to unlink %s ! Type: %s, Value: %s"
                                    % (reader.sortedFiles[index], type, value))
