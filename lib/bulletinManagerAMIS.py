# -*- coding: UTF-8 -*-
"""Gestion des bulletins "AMIS" """

import bulletinManager, bulletinAm, os, string

__version__ = '2.0'

class bulletinManagerAMIS(bulletinManager.bulletinManager):
	__doc__ = bulletinManager.bulletinManager.__doc__ + \
        """
        #### CLASSE bulletinManagerAMIS ####

        Nom:
        bulletinManagerAMIS

        Paquetage:

        Statut:
        Classe concrete

        Responsabilites:
        -Lire et ecriture des bulletins en format AMIS;

        Attributs:

        Methodes:

        Auteur:
        Pierre Michaud

        Date:
	Octobre 2004 
        """

	def __init__(self,pathTemp,logger,pathSource=None,\
			pathDest=None,maxCompteur=99999,lineSeparator='\n',extension=':',use_pds=0):

		bulletinManager.bulletinManager.__init__(self,pathTemp,logger, \
						pathSource,pathDest,maxCompteur,lineSeparator,extension,use_pds)

	def __isSplittable(self,rawBulletin):
		pass

	def __splitBulletin(self,rawBulletin):
		pass

        def _bulletinManager__generateBulletin(self,rawBulletin):
		pass

        def writeBulletinToDisk(self,unRawBulletin):
		pass

	def __initMapEntetes(self, pathFichierStations):
		pass
	        
        def getFileName(self,bulletin,error=False):
		pass
