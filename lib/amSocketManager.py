#######################################
#
#	Gestion des sockets AM en 
#	lecture et decoupage des
#	bulletins
#
#	Par: Louis-Philippe Theriault
#	     Stagiaire, CMC
#
#######################################
import socket
import asyncore
import time
import struct
import commands

# La taille du amRec est prise d'a partir du fichier ytram.h, à l'origine dans
# amtcp2file. Pour la gestion des champs l'on se refere au module struct
# de Python.
patternAmRec = '80sLL4sii4s4s20s'
sizeAmRec = struct.calcsize(patternAmRec)

class amSock(asyncore.dispatcher):
    """Specialisation de asyncore pour la gestion de socket AM.
    """
    def __init__(self,port,host='',master=False):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
	while True:
		try:
			self.bind((host,port))
			break
		except socket.error:
			time.sleep(1)

	self.port = port
	self.listen(True)
	self.sendBuffer = str()
	self.recvBuffer = str()

	while True:
		try:
			self.conn, self.addr = self.accept()
			break
		except TypeError:
			time.sleep(1)

	self.close()
	self.setblocking(False)

    def getNextBulletin(self):
	"""Retourne le prochain bulletin dans le buffer.

	   S'il n'y a pas de nouveau bulletins lors de la lecture, un chaine vide est retournee"""
	if self.recvBuffer != '':
		if len(self.recvBuffer) >= sizeAmRec:
			(header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
				struct.unpack(patternAmRec,self.recvBuffer[0:sizeAmRec])
		else:
			return ''

		length = socket.ntohl(length)

		if len(self.recvBuffer) >= sizeAmRec + length:
			bulletin = self.recvBuffer[sizeAmRec:sizeAmRec + length]
			self.recvBuffer = self.recvBuffer[sizeAmRec + length:]

			return bulletin
		else:
			return ''
	else:
		return ''

    def readBuffer(self):
	"""Lecture du buffer et copie dans le buffer de l'objet,
	   effectue aussi une verification de l'etat de la connection,""" 
	while True:
		try:
			temp = self.conn.recv(32768)
	
			if temp == '':
				# Peut etre un broken pipe, test...
				# le test est un netstat -an | grep <port>
				# et si le port est en close_wait, l'on
				# ferme le socket, la connection est perdue
				out = commands.getoutput('netstat -an | grep 127.0.0.1:' + str(self.port))
				if out == '' or  out.split()[-1] == 'CLOSE_WAIT':
					# La connection est brisee, une exception doit etre levee
					self.conn.shutdown(2)
					self.conn.close()
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
