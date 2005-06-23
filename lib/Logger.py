#############################################################################################
# Name: Logger.py
#
# Author: Daniel Lemay
#
# Date: 2004-09-28
#
#############################################################################################

import logging, logging.handlers

class Logger:
   
   def __init__(self, logname, log_level, loggername):
      self.logger = logging.getLogger(loggername)
      self.logger.setLevel(eval("logging." + log_level))                     # Set logging level
      hdlr = logging.handlers.RotatingFileHandler(logname, "a", 1000000, 3)  # Max 100000 bytes, 3 rotations
      #fmt = logging.Formatter("%(levelname)-8s %(asctime)s %(name)s %(message)s")
      #fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s","%x %X")
      fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

      hdlr.setFormatter(fmt)
      self.logger.addHandler(hdlr)

   def getLogger(self):
      return self.logger 

if (__name__ == "__main__"):
   
   bad = "This is BAD!"

   logger = Logger("/apps/testDan/toto.log", "DEBUG", "CMISX")
   logger = logger.getLogger()
   logger.debug("Ceci est un debug")
   logger.info("Ceci est un info")
   logger.warning("Ceci est un warning!")
   logger.error("Ceci est un error!")
   logger.critical("Ceci est un critical!")

   try:
      raise bad

   except bad:   
      print "Bad exception has been raised"
      logger.exception("Ceci est un exception!")
