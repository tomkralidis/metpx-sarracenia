# -*- coding: UTF-8 -*-
"""
#############################################################################################
# Name: senderAMIS.py
#
# Author: Daniel Lemay
#
# Date: 2005-03-16
#
# Description:
#
#############################################################################################

"""
import os, sys, time, socket, curses.ascii
import fet
from DiskReader import DiskReader
from MultiKeysStringSorter import MultiKeysStringSorter
from CacheManager import CacheManager

class senderAMIS: 
   
   def __init__(self, options, logger):
      self.options = options                          # Options
      self.remoteHost = options.host                  # Remote host (name or ip) 
      self.port = int(options.port)                   # Port to which the receiver is bind
      self.maxLength = 1000000                        # Maximum length that we can transmit on the link
      self.address = (self.remoteHost, self.port)     # Socket address
      self.timeout = options.connect_timeout          # No timeout for now
      self.logger = logger                            # Logger object
      self.socketAMIS = None                          # The socket
      self.reader = None                              # Object used to read and sort bulletins from disk 

      self.totBytes = 0
      self.initialTime = time.time()
      self.finalTime = None

      self.cacheManager = CacheManager(maxEntries=10000, timeout=3*3600)

      self._connect()
      #self.run()

   def _connect(self):
      self.socketAMIS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
      self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      #print self.socketAMIS.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
      #self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,4096)
      #print self.socketAMIS.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
      #self.socketAMIS.setblocking(True)

      while True:
         try:
            self.socketAMIS.connect(self.address)
            self.logger.writeLog(self.logger.INFO, "AMIS Sender is now connected to: %s" % str(self.address))
            break
         except socket.gaierror, e:
            #print "Address related error connecting to server: %s" % e
            self.logger.writeLog(self.logger.ERROR, "Address related error connecting to server: %s" % e)
            sys.exit(1)
         except socket.error, e:
            (type, value, tb) = sys.exc_info()
            self.logger.writeLog(self.logger.ERROR, "Type: %s, Value: %s, Sleeping 5 seconds ..." % (type, value))
            #self.logger.writeLog(self.logger.ERROR, "Connection error: %s, sleeping ..." % e)
            time.sleep(5)

   def shutdown(self):
      pass

   def read(self):
      self.reader = DiskReader(fet.FET_DATA + fet.FET_TX + self.options.client,
                               fet.clients[self.options.client][5],
                               True,
                               0,
                               True,
                               self.logger,
                               eval(fet.clients[self.options.client][4]))
      self.reader.sort()
      return(self.reader.getFilesContent(fet.clients[self.options.client][5]))

   def write(self, data):
      if len(data) >= 1:
         self.logger.writeLog(self.logger.INFO,"%d new bulletins will be sent", len(data))
         for index in range(len(data)):

            # If data[index] is already in cache, we don't send it
            if self.cacheManager.find(data[index]) is not None:
                try:
                   os.unlink(self.reader.sortedFiles[index])
                   self.logger.writeLog(self.logger.INFO,"%s has been erased (was cached)", os.path.basename(self.reader.sortedFiles[index]))
                except OSError, e:
                   (type, value, tb) = sys.exc_info()
                   self.logger.writeLog(self.logger.ERROR, "Unable to unlink %s ! Type: %s, Value: %s" 
                                        % (self.reader.sortedFiles[index], type, value))
                continue

            bullAMIS = self.encapsulate(data[index])
            nbBytesToSend = len(bullAMIS)
            nbBytes = nbBytesToSend
            while nbBytesToSend > 0: 
               nbBytesSent = self.socketAMIS.send(bullAMIS)
               bullAMIS = bullAMIS[nbBytesSent:]
               nbBytesToSend = len(bullAMIS)
               self.totBytes += nbBytesSent
               #print self.totBytes
            self.logger.writeLog(self.logger.INFO,"(%5d Bytes) Bulletin %s livré", 
                                 nbBytes, os.path.basename(self.reader.sortedFiles[index]))
            try:
               os.unlink(self.reader.sortedFiles[index])
               self.logger.writeLog(self.logger.DEBUG,"%s has been erased", os.path.basename(self.reader.sortedFiles[index]))
            except OSError, e:
               (type, value, tb) = sys.exc_info()
               self.logger.writeLog(self.logger.ERROR, "Unable to unlink %s ! Type: %s, Value: %s" 
                                    % (self.reader.sortedFiles[index], type, value))
         self.logger.writeLog(self.logger.INFO, "Caching stats: %s " % str(self.cacheManager.getStats()))
         #self.logger.writeLog(self.logger.INFO, "Cache: %s " % str(self.cacheManager.cache))

      else:
         time.sleep(1)

      if (self.totBytes > 108000):
         self.logger.writeLog(self.logger.INFO, self.printSpeed() + " Bytes/sec")
         #result = open('/apps/px/result', 'w')
         #result.write(self.printSpeed())
         #sys.exit()

   def printSpeed(self):
      elapsedTime = time.time() - self.initialTime
      speed = self.totBytes/elapsedTime
      self.totBytes = 0
      self.initialTime = time.time()
      return "Speed = %i" % int(speed)

   def encapsulate(self, data):
      originalData = data
      preamble = chr(curses.ascii.SOH) + "\r\n"
      endOfLineSep = "\r\r\n"
      endOfMessage = endOfLineSep + chr(curses.ascii.ETX) + "\r\n\n" + chr(curses.ascii.EOT)

      data = data.strip().replace("\n", endOfLineSep)
      
      if (len(data) + 11)  > self.maxLength :
         diff = len(data) + 11 - self.maxLength 
         data = originalData[0:-diff]
         data = data.strip().replace("\n", endOfLineSep)

      return preamble + data + endOfMessage

   def run(self):
      while True:
         data = self.read()
         try:
            self.write(data)
         except socket.error, e:
            (type, value, tb) = sys.exc_info()
            self.logger.writeLog(self.logger.ERROR, "Sender error %s ! Type: %s, Value: %s" 
                                 % (self.reader.sortedFiles[index], type, value))
            
            self.logger.writeLog(self.logger.ERROR, "Sending error: %s" % e)
            # FIXME: We can try to reconnect

         #time.sleep(0.2)

if __name__ == "__main__":
   sender = senderAMIS("cisco-test.test.cmc.ec.gc.ca", 4001)
