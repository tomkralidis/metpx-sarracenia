"""Définition des diverses classes découlant de socketManager.

Ces classes servent à l'établissement de la connection, la 
réception et envoi des bulletins et la vérification du respect 
des contraintes relatives aux protocoles.
"""

__version__ = '2.0'

class socketManager:
	"""Classe abstraite regroupant toutes les fonctionnalitées 
requises pour un gestionnaire de sockets. Les méthodes 
qui ne retournent qu'une exception doivent êtres redéfinies 
dans les sous-classes.

Les arguments à passer pour initialiser un socketManager sont les
suivants:

	type		'master','slave' (default='slave')

			- Si master est fourni, le programme se 
			  connecte à un hôte distant, si slave,
			  le programme écoute pour une 
			  connection.

	localPort	int (default=9999)

			- Port local ou se 'bind' le socket.

	remoteHosts	[ (str hostname,int port) ]

			- Liste de (hostname,port) pour la 
			  connection. Lorsque timeout secondes
			  est atteint, le prochain couple dans
			  la liste est essayé.

			- Doit être absolument fourni si type='master',
			  et non fourni si type='slave'.

	timeout		int (default=None)
			
			- Lors de l'établissement d'une connection 
			  à un hôte distant, délai avant de dire 
			  que l'hôte de réponds pas.

"""
	def __init__(type='slave',localPort=9999,remoteHosts=None,timeout=None):
		self.type = type
		self.localPort = localPort
		self.remoteHosts = remoteHosts
		self.timeout = timeout
