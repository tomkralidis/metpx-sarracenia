"""
#############################################################################################
# Name: PXIgniter.py
#
# Author: Daniel Lemay
#
# Date: 2005-03-02
#
# Description: Use to start, stop, restart, reload and obtain status informations
#              about receivers and senders.
#
#############################################################################################

"""
import sys, os, commands, signal
from Igniter import Igniter
import fet

class PXIgniter(Igniter):
   
   def __init__(self, direction, type, client, cmd, lockPath, options=None, logger=None):
      Igniter.__init__(self, cmd, lockPath) # Parent constructor
      self.direction = direction            # Receiver or Sender (string)
      self.type = type                      # wmo, am, etc. (string)
      self.client = client                  # Client to send or Source from which to receive
      self.options = options                # All options
      self.logger = logger                  # Logger object
      self.gateway = None                   # Gateway object
      eval("self." + cmd)()                 # Execute the command directly

   def setGateway(self, gateway):
      self.gateway = gateway
      #print "Gateway is: " + repr(gateway)

   def printComment(self, commentID):
      if commentID == 'Already start':
         print "WARNING: The %s %s is already started with PID %d, use stop or restart!" % (self.direction, self.client, self.lockpid)
      elif commentID == 'Locked but not running':
         print "INFO: The %s %s was locked, but not running! The lock has been unlinked!" % (self.direction, self.client)
      elif commentID == 'No lock':
         print "No lock on the %s %s. Are you sure it was started?" % (self.direction, self.client)
      elif commentID == 'Restarted successfully':
         print "%s %s has been restarted successfully!" % (self.direction, self.client)
      elif commentID == 'Status, started':
         print "%s %s is running with PID %d" % (self.direction, self.client, self.lockpid)
      elif commentID == 'Status, not running':
         print "%s %s is not running" % (self.direction, self.client)
      elif commentID == 'Status, locked':
         print "%s %s is locked (PID %d) but not running" % (self.direction, self.client, self.lockpid)

   def start(self):
      
      Igniter.start(self)

      # Signals assignment
      signal.signal(signal.SIGTERM, self._shutdown)
      signal.signal(signal.SIGINT, self._shutdown)
      signal.signal(signal.SIGHUP, self._reload)

   def _shutdown(self, sig, stack):
      """
      Do the real work here. Depends of type of sender/receiver
      """
      #print "shutdown() has been called"
      os.kill(self.lockpid, signal.SIGKILL)

   def _reload(self, sig, stack):
      """
      Do the real work here. Depends of type of sender/receiver
      """
      if self.gateway is None:
         print "_reload() has been called for %s (%s %s)" % (self.client, self.direction, self.type)
         print "No gateway object! Nothing can be done"
      else:
         #print self.gateway
         if self.direction == 'sender':
            fet.startup(self.options, self.logger)
            self.logger.writeLog(self.logger.INFO, "%s has been reload" % self.direction)
         elif self.direction == 'receiver':
            fet.startup(self.options, self.logger)
            if self.type == 'am':
               self.gateway.unBulletinManager.reloadMapCircuit('/dev/null')
               self.gateway.unBulletinManager.reloadMapEntetes(self.gateway.pathFichierStations)
            if self.type == 'wmo':
               self.gateway.unBulletinManager.reloadMapCircuit('/dev/null')

            self.logger.writeLog(self.logger.INFO, "%s has been reload" % self.direction)
         else:
            print "What is it? A collector!"
      
   def reload(self):
      """
      Le reload ne doit pas s'appliquer a un source/client en particulier.
      Cette operation doit etre effectue pour chaque source/client qui roule
      au moment de la demande de reload.

      Il me faut la liste des sources/clients qui tournent, j'obtiens ceci en verifiant les .lock + ps -p pid.
      A tous les programmes qui verifient les 2 conditions precedentes, j'envoie le SIGHUP. Les fonctions appelees
      a ce moment devrait faire le travail specifique pour chaque sender/receiver de chaque type (wmo, am, amis, aftn).
      La fonction appelee devrait se trouver dans la classe appropriee....
      """
      # Verify user is not root
      if os.getuid() == 0:
         print "FATAL: Do not reload as root. It will be a mess."
         sys.exit(2)
         
      if Igniter.isLocked(self) and not commands.getstatusoutput('ps -p ' + str(self.lockpid))[0]:
         # SIGHUP is sent to initiate the reload
         os.kill(self.lockpid, signal.SIGHUP) 
      else:
         print "No process to reload for %s (%s %s)!" % (self.client, self.direction, self.type)

      # In any case, we exit!!
      sys.exit(2)

if __name__ == "__main__":

   pass

"""
def shutdown(sig, stack):
   logger.writeLog(logger.INFO,"Reception d'un signal de shutdown (signal=%d)", sig)
   sys.exit()

def reload(sig, stack):
   global config, bullManager
   config = gateway.gateway.loadConfig(args[0])
   bullManager = bulletinManager.bulletinManager(config.pathTemp, logger, config.pathSource, config.pathDestination, config.maxCompteur,
                                                 config.lineSeparator, config.extension, config.ficCircuits, config.use_pds)
   logger.writeLog(logger.INFO,"Reception d'un signal de reload (signal=%d)", sig)


   (status, output) = commands.getstatusoutput("date")
   print output
"""
