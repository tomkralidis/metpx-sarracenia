#############################################################
#	Divers utilitaires pour la gestion et manipulation
#	de bulletins une fois ecrit sur le disque par 
#	amtcp2file.
#
#	Par:  Louis-Philippe Theriault
#	      Stagiaire, CMC
#
#############################################################

import utils
import time
import string
import os
import commands

extension = ""
extensionDynamique = False

# Champs dans le fichier de header2circuit
champsHeader2Circuit = 'entete:routing_groups:rename:'

def chargerFicCollection(pathFicCollection):
	""" *	Retourne une map contenant les entete a utiliser avec
 	    *	quelles stations. La cle se trouve a etre une concatenation des
 	    *	2 premieres lettres du bulletin et de la station, la definition
 	    *	est une string qui contient l'entete a ajouter au bulletin.
 	    *
 	    *	Ex.: TH["SPCZPC"] = "CN52 CWAO "
	"""
	uneEntete = ""
	uneCle = ""
	unPrefixe = ""
	uneLigneParsee = ""
	mapCollection = {}

	for ligne in utils.lireFicTexte(pathFicCollection):
		uneLigneParsee = ligne.split()

		unPrefixe = uneLigneParsee[0][0:2]
		uneEntete = uneLigneParsee[0][2:6] + ' ' + uneLigneParsee[0][6:] + ' '

		for station in uneLigneParsee[1:]:
			uneCle = unPrefixe + station

			mapCollection[uneCle] = uneEntete

	return mapCollection

def getStationMeteo(bulletin):
	"""Prends un bulletin et retourne la station associee.

	   Leve une exception si le cas n'est pas specifie.
	"""
	station  = ""
	premiereLignePleine = ""

	# Cas special, il faut aller chercher la prochaine ligne pleine
	for ligne in bulletin[1:]:
		premiereLignePleine = ligne

		if len(premiereLignePleine) > 1:
			break

	# Embranchement selon les differents types de bulletins
	if bulletin[0][0:2] == "SA":
		if bulletin[1].split()[0] == "METAR" or bulletin[1].split()[0] == "LWIS":
			station = premiereLignePleine.split()[1]
		else:
			station = premiereLignePleine.split()[0]

	elif bulletin[0][0:2] == "SP":
		station = premiereLignePleine.split()[1]

	elif bulletin[0][0:2] == "SI"or bulletin[0][0:2] == "SM":
		station = premiereLignePleine.split()[0]

	elif bulletin[0][0:2] == "FC" or bulletin[0][0:2] == "FT":
		if premiereLignePleine.split()[1] == "AMD":
			station = premiereLignePleine.split()[2]
		else:
			station = premiereLignePleine.split()[1]

	elif bulletin[0][0:2] == "UE" or bulletin[0][0:2] == "UG" or bulletin[0][0:2] == "UK" or bulletin[0][0:2] == "UL" or bulletin[0][0:2] == "UQ" or bulletin[0][0:2] == "US":
		station = premiereLignePleine.split()[2]

	elif bulletin[0][0:2] == "RA" or bulletin[0][0:2] == "MA" or bulletin[0][0:2] == "CA":
 		station = premiereLignePleine.split()[0].split('/')[0]
		
		if station[0] == '?':
			station = station[1:]
	else:
		raise Exception("StationNonTrouvee")

	return station


def getFormattedSystemTime():
	"""Retourne une string de l'heure locale du systeme, selon
	   jjhhmm : jour/heures(24h)/minutes"""
	return time.strftime("%d%H%M",time.localtime())

def initExtension():
	"""A etre execute une fois au debut du programme, initialise 
	   l'extension"""
	return '-TT' in extension.split(':') or '-CCCC' in extension.split(':')

def getExtension(type='NonImplante',origine='nonImplante'):
	"""Retourne l'extension appropriee pour le fichier du bulletin courant"""
	if not extensionDynamique:
		return extension
	else:
		params = extension.split(':')

		if '-TT' in params:
			params[params.index('-TT')] = type

		if '-CCCC' in params:
			params[params.index('-CCCC')] = origine

		return string.join(params,':')

def separerBulletin(bulletinOriginal,motCle):
	"""Separe le bulletin apres l'entete, delimite par le motCle.
	   et retourne une liste de bulletins fusionnes.

	   Le bulletin est une liste de lignes.

	   L'entete devrait etre l'originale"""

	entete = bulletinOriginal[0]	
	listeBulletins = []
	unBulletin = []

	for ligne in bulletinOriginal[1:]:
		if ligne.split()[0] == motCle:
			listeBulletins.append(string.join(unBulletin,'\n'))

			unBulletin = list()
			unBulletin.append(entete)

		unBulletin.append(ligne)

	listeBulletins.append(string.join(unBulletin,'\n'))

	return listeBulletins[1:]

def ecrireBulletins(listeBulletins,nomFichierOrig):
	"""Ecrit une liste de bulletins sur le disque avec comme nom, le nom
	   original avec a,b,c,... avant l'extension d'insere pour chaque bulletin.

	   Le nom doit etre le chemin complet du path"""
	listeChars = 'abcdefghijklmnopqrstuvwxyz'
	charPtr = 0
	unBulletinTexte = ''
	nomFicDest = nomFichierOrig.split(':')[0] + '$:' + string.join(nomFichierOrig.split(':')[1:],':')

	for bulletin in listeBulletins:
		unBulletinTexte = string.join(bulletin,'\n')

		commands.getoutput('touch ' + nomFicDest.replace('$',listeChars[charPtr]))
		f = os.open(nomFicDest.replace('$',listeChars[charPtr]), os.O_WRONLY)
		os.write(f,unBulletinTexte)
		os.close(f)

		charPtr = charPtr + 1

def getType(bulletin):
	"""Retourne AN,BI selon le type de bulletin."""
	return 'AN'

def loadCircuitFile(header2circuit_file):
	"""Charge le fichier de header2circuit et retourne un map avec comme cle
	   le premier champ de champsHeader2Circuit (premier token est la cle,
	   le reste des tokens sont les cles d'un map contenant les valeurs 
	   associes."""
	unMap = {}
	
	try:
		fic = os.open( header2circuit_file, os.O_RDONLY )
	except Exception:
		raise Exception('uDef','Impossible d\'ouvrir le fichier d\'entetes')

	champs = champsHeader2Circuit.split(':')

	lignes = os.read(fic,os.stat(header2circuit_file)[6])

	for ligne in lignes.splitlines():
		uneLigneSplitee = ligne.split(':')

		unMap[uneLigneSplitee[0]] = {}

		try:
			for token in range( max( len(champs)-2,len(uneLigneSplitee)-2 ) ):
				unMap[uneLigneSplitee[0]][champs[token+1]] = uneLigneSplitee[token+1]

				if len(unMap[uneLigneSplitee[0]][champs[token+1]].split(' ')) > 1:
					unMap[uneLigneSplitee[0]][champs[token+1]] = unMap[uneLigneSplitee[0]][champs[token+1]].split(' ')
		except IndexError:
			print ligne
			raise Exception('uDef','Les champs ne concordent pas dans le fichier')

	return unMap

