#######################################
#
#	Gestion des sockets WMO en 
#	lecture et decoupage des
#	bulletins
#
#	Par: Louis-Philippe Theriault
#	     Stagiaire, CMC
#
#######################################
import socket
import time
import struct
import string
import curses
import curses.ascii
import commands
import signal

# La taille du wmoHeader est prise d'a partir du document :
# "Use of TCP/IP on the GTS", pages 28-29, et l'exemple en C
# page 49-54
patternWmoHeader = '8s2s'
sizeWmoHeader = struct.calcsize(patternWmoHeader)

class wmoSock:
    """Specialisation de asyncore pour la gestion de socket WMO
       Si master a True, la connection se fait vers l'hote distant.

       Remote est un tuple contenant (host,port)"""
    def __init__(self,port,master=False,remote=(), timeout=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
	while True:
		try:
			self.socket.bind(('',port))
			break
		except socket.error:
			time.sleep(1)

	self.recvBuffer = str()
	self.sendBuffer = []
	self.counter = 0
	self.port = port
	then = time.time()
	self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

	if not master:
		self.socket.listen(1)

		while True:
			if timeout != None and (time.time() - then) > timeout:
				self.socket.close()
				raise Exception('uDef','Connection impossible, timeout depasse!')

			try:
				conn, self.addr = self.socket.accept()
				break
			except TypeError:
				time.sleep(1)

		self.socket.close()
		self.socket = conn
	else:
		if remote == ():
			raise Exception('uDef','remote (host,port) doit etre specifie')

		while True:
                        if timeout != None and (time.time() - then) > timeout:
				self.socket.close()
                                raise Exception('uDef','Connection impossible, timeout depasse!')

			try:
				self.socket.connect(remote)
				break
			except socket.error:
				time.sleep(5)

	self.socket.setblocking(False)

    def checkNextMsgIntegrity(self):
	"""Regarde si le prochain message dans le buffer possede une syntaxe
	   conforme au specs. Leve une exception si ce n'est pas le cas."""
	if self.recvBuffer != '':
                if len(self.recvBuffer) >= sizeWmoHeader:
                        (msg_length,msg_type) = \
                                struct.unpack(patternWmoHeader,self.recvBuffer[0:sizeWmoHeader])
                else:
                        raise Exception('uDef','Longueur de l\'entete insuffisante')

		try:
			msg_length = int(msg_length)
		except ValueError:
			raise('uDef','Longeur du message contient des caracteres')

		if msg_type.find('BI') == -1 and msg_type.find('AN') == -1 and msg_type.find('FX') == -1:
			raise Exception('uDef','Type de message incorrect')

		if len(self.recvBuffer) >= sizeWmoHeader + msg_length:
			if ord(self.recvBuffer[sizeWmoHeader]) != curses.ascii.SOH and (self.recvBuffer[sizeWmoHeader+msg_length]) != curses.ascii.ETX:
				raise Exception('uDef','Caractere de controle (SOH/ETX) non trouve')
			return 
		else:
			raise Exception('uDef','Longueur du message insuffisant')
	else:
		raise Exception('uDef','Le buffer est vide')

    def getNextBulletin(self):
	"""Retourne le prochain bulletin dans le buffer.

	   S'il n'y a pas de nouveau bulletins lors de la lecture, un chaine vide est retournee"""
	if self.recvBuffer != '':

		try:
			self.checkNextMsgIntegrity()
		except Exception, inst:
			if inst[0] == 'uDef':
				if inst[1] != 'Longueur de l\'entete insuffisante' and inst[1] != 'Longueur du message insuffisant' and inst[1] != 'Le buffer est vide':
					raise
				else:
					return ''
			else:
				raise

		(msg_length,msg_type) = \
			struct.unpack(patternWmoHeader,self.recvBuffer[0:sizeWmoHeader])

		msg_length = int(msg_length)
		bulletin = self.recvBuffer[sizeWmoHeader:sizeWmoHeader + msg_length]
		self.recvBuffer = self.recvBuffer[sizeWmoHeader + msg_length:]

		return bulletin[12:-4]
	else:
		return ''

    def readBuffer(self):
	"""Lecture du Buffer et copie dans le buffer de l'objet"""
	while True:
                try:
                        temp = self.socket.recv(32768)

                        if temp == '':
                                # Peut etre un broken pipe, test...
                                # le test est un netstat -an | grep <port>
                                # et si le port est en close_wait, l'on
                                # ferme le socket, la connection est perdue
                                out = commands.getoutput('netstat -an | grep 127.0.0.1:' + str(self.port))
                                if out == '' or  out.find('CLOSE_WAIT') != -1:
                                        # La connection est brisee, une exception doit etre levee
                                        self.socket.shutdown(2)
                                        self.socket.close()
                                        raise Exception('uDef','La connection est brisee')
                                else:
                                        time.sleep(5)
                                        continue

                        self.recvBuffer = self.recvBuffer + temp
                        break

                except socket.error, inst:
                        if inst.args[0] == 11:
                                time.sleep(1)
                        else:
                                raise

    def seekNextBulletin(self):
	"""Arrange le buffer de sorte que le prochain bulletin soit au debut.

	NB: Selon les specs de WMO, le sender des bulletins devrait commencer son
	    feed au debut d'un bulletin."""
	while True:
		nextSOH = self.recvBuffer.find(chr(curses.ascii.SOH))

		if nextSOH == -1:
		# SOH non trouve, prochain message pas encore dans le buffer
			raise Exception('uDef','SOH non trouve, prochain message pas encore dans le buffer')
		else:
			if nextSOH < sizeWmoHeader:
			# L'entete est incomplete
				self.recvBuffer = self.recvBuffer[nextSOH + 1:]
				pass
			else:
			# L'entete est complete, modification du buffer
				self.recvBuffer = self.recvBuffer[nextSOH - sizeWmoHeader:]
				return

    def sendBulletin(self,bulletin,type):
	"""S'occupe de creer l'entete a l'entours du bulletin et envoie
	   le buffer sortant a l'hote. Le type doit etre analyse dans le
	   programme client et passe en parametre.

	   Retourne le nombre de bulletins envoyes correctement apres 
	   l'execution de la methode."""
	self.sendBuffer.append(self.wrapBulletin(bulletin,type))
	return self.transmitBuffer()

    def wrapBulletin(self,bulletin,type='AN'):
	"""Cree l'entete pour le bulletin

	   Nb: Le fenetrage n'est pas implemente"""
	if not type in ['AN','BI','FX']:
		raise Exception('uDef','Type illegal')

	bulletin = chr(curses.ascii.SOH) + '\r\r\n' + self.getNextCounter(5) + '\r\r\n' + bulletin + '\r\r\n' + chr(curses.ascii.ETX)
	
	return string.zfill(len(bulletin),8) + type + bulletin

    def transmitBuffer(self):
	"""Vide le buffer de sortie en envoyant les bulletins
	   jusqu'a ce que le recepteur ne puisse plus en accepter."""
	nbBullEnvoyes = 0

	while True:

		if len(self.sendBuffer) == 0:
			break

		try:
			sentData = self.socket.send(self.sendBuffer[0])
		except socket.error,inst:
			if inst.args[0] == 32 or inst.args[0] == 104:
				self.socket.close()
			# Broken pipe!
				raise Exception('uDef','La connection est brisee')
			elif inst.args[0] == 11:
				break
			else:
				raise

		self.sendBuffer[0] = self.sendBuffer[0][sentData:]

		if self.sendBuffer[0] == '':
			self.sendBuffer.pop(0)
			nbBullEnvoyes = nbBullEnvoyes + 1

	return nbBullEnvoyes

    def getNextCounter(self,x):
	"""Retourne une string de x large contenant le prochain compteur et l'incremente"""
	self.counter = self.counter + 1
	return string.zfill(self.counter,x)

    def shutdownProperly(self):
        """Fait un shutdown gracieux du socket"""
        self.socket.shutdown(2)

	try:
		self.recvBuffer = self.recvBuffer + self.socket.recv(1000000)
	except socket.error, inst:
		pass

	self.socket.close()
