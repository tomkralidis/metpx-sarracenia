
__version__ = '2.0'

import struct, socket
import socketManager
import time

class socketManagerAMIS(socketManager.socketManager):
	__doc__ = socketManager.socketManager.__doc__ + \
	"""
        #### CLASSE socketManagerAMIS ####

        Nom:
        socketManagerAMIS

        Paquetage:

        Statut:
        Classe concrete

        Responsabilites:

        Attributs:
        Attribut de la classe parent socketManager

        Methodes:
        Methodes de la classe parent socketManager

        Auteur:
        Pierre Michaud
	
	"""

	def __init__(self,logger,type='slave',localPort=9999,remoteHost=None,timeout=None):
		socketManager.socketManager.__init__(self,logger,type,localPort,remoteHost,timeout)

        def wrapBulletin(self,data):
		__doc__ = socketManager.socketManager.wrapBulletin.__doc__ + \
		"""
		wrapBulletin test
		"""
		pass

	def sendBulletin(self,data):
		#__doc__ = socketManager.socketManager.sendBulletin.__doc__ + \
		"""
		sendBulletin test
		"""
		while True:
			self.wrapBulletin(data)
			#try:
			bytesSent = self.socket.send(data)
			#sleep est imperatif, sinon la connexion se brise
			time.sleep(0.5)
			if bytesSent < len(data):
				print "DANGER, SEULEMENT %d octets d'envoyes sur %d" % (bytesSent,len(data))
			

        def checkNextMsgStatus(self):
                __doc__ = socketManager.socketManager.checkNextMsgStatus.__doc__ + \
                """
		   Date:	Octobre 2004
                """
		pass
