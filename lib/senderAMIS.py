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

class senderAMIS: 
   
   data = "Salut, bonjour!\r\r\n" # 16 bytes
   test = 0

   def __init__(self, options, logger):
      self.options = options                          # Options
      self.remoteHost = options.host                  # Remote host (name or ip) 
      self.port = int(options.port)                   # Port to which the receiver is bind
      self.maxLength = 1024                           # Maximum length that we can transmit on the link
      self.address = (self.remoteHost, self.port)     # Socket address
      self.timeout = options.connect_timeout          # No timeout for now
      self.logger = logger                            # Logger object
      self.socketAMIS = None                          # The socket
      self.reader = None                              # Object used to read and sort bulletins from disk 

      self.totBytes = 0
      self.initialTime = time.time()
      self.finalTime = None

      self._connect()
      self.run()

   def _connect(self):

      self.socketAMIS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
      self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      print self.socketAMIS.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
      #self.socketAMIS.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,4096)
      print self.socketAMIS.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
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
            #print "Connection error: %s, sleeping ..." % e
            self.logger.writeLog(self.logger.ERROR, "Connection error: %s, sleeping ..." % e)
            time.sleep(5)

   def shutdown(self):
      pass

   def readTest(self):
      return senderAMIS.data

   def read(self):
      self.reader = DiskReader(fet.FET_DATA + fet.FET_TX + self.options.client,
                               fet.clients[self.options.client][5],
                               True,
                               self.logger,
                               eval(fet.clients[self.options.client][4]))
      self.reader.sort()
      return(self.reader.getFilesContent(fet.clients[self.options.client][5]))

   def writeTest(self, data):
      nbBytes = self.socketAMIS.send(data)
      self.totBytes += nbBytes
      print self.totBytes
      if (self.totBytes > 108000):
         result = open('/apps/px/result', 'w')
         result.write(self.printSpeed())
         sys.exit()

   def write(self, data):
      if len(data) >= 1:
         self.logger.writeLog(self.logger.INFO,"%d new bulletins will be sent", len(data))
         for index in range(len(data)):
            bullAMIS = self.encapsulate(data[index])
            nbBytesToSend = len(bullAMIS)
            while nbBytesToSend > 0: 
               nbBytesSent = self.socketAMIS.send(bullAMIS)
               bullAMIS = bullAMIS[nbBytesSent:]
               nbBytesToSend = len(bullAMIS)
               self.totBytes += nbBytesSent
               print self.totBytes
            self.logger.writeLog(self.logger.INFO,"%s has been sent", os.path.basename(self.reader.sortedFiles[index]))
            #os.unlink(self.reader.sortedFiles[index])
            self.logger.writeLog(self.logger.DEBUG,"%s has been erased", os.path.basename(self.reader.sortedFiles[index]))

      else:
         time.sleep(1)

      if (self.totBytes > 54000):
         result = open('/apps/px/result', 'w')
         result.write(self.printSpeed())
         sys.exit()

   def printSpeed(self):
      elapsedTime = time.time() - self.initialTime
      speed = self.totBytes/elapsedTime
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
      if senderAMIS.test:
         while True:
            data = self.readTest()
            try:
               self.writeTest(data)
            except socket.error:
               print "Sending error: %s" % e
               
            #time.sleep(0.002)
            #break
      else:
         while True:
            data = self.read()
            try:
               self.write(data)
            except socket.error:
               print "Sending error: %s" % e
               # FIXME: We can try to reconnect

            #time.sleep(0.2)
            #break

if __name__ == "__main__":
   sender = senderAMIS("cisco-test.test.cmc.ec.gc.ca", 4001)
