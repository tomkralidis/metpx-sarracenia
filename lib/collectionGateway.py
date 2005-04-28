# -*- coding: UTF-8 -*-
"""ReceiverWmo: socketWmo -> disk, incluant traitement pour les bulletins"""

import os
import gateway, bulletinManager, collectionManager
import fet

class collectionGateway(gateway.gateway):
    __doc__ = gateway.gateway.__doc__ + \
    """
    ### Ajout de collectionGateway ###

    Un collectionGateway lit les bulletins sur le disque, et
    l'envoie à la collection s'il y a lieu, à un bulletinManager
    de base sinon.

    Auteur: Louis-Philippe Thériault
    Date:   Octobre 2004
    """

    def __init__(self,path,options,logger):
        gateway.gateway.__init__(self,path,options,logger)

        self.bulletinsAEffacer = []

        # Instanciation des collectionManager(writer)
        self.logger.writeLog(logger.DEBUG,"Instanciation du collectionManager")

        self.unCollectionManager = \
            collectionManager.collectionManager( logger )

        # Instanciation du bulletinManager(reader/writer)
        self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManager")
        self.unBulletinManager = \
                  bulletinManager.bulletinManager(
                          pathTemp=fet.FET_DATA+fet.FET_TMP,
                          logger=logger,
                          pathSource=fet.FET_DATA+fet.FET_CL,
                          pathDest='/apps/pds/RAW/-PRIORITY',
                          pathFichierCircuit=fet.FET_ETC+'header2client.conf',
                          extension=options.extension,
                          use_pds = fet.options.use_pds
                          )

        # Partage du même map pour les 2 managers
        self.unBulletinManager.setMapCircuits(self.unCollectionManager.getMapCircuits())

    def read(self):
        __doc__ =  gateway.gateway.read.__doc__ + \
        """### Ajout de collectionGateway ###

           Lecture des bulletins sur le disque par le bulletinManager.

           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        # Effacement des fichiers que l'on a traîté
        # Si on est rendu ici, on prends pour acquis
        # que les fichiers ont étés traîtés
        for fic in self.bulletinsAEffacer:
            self.logger.writeLog(self.logger.VERYVERYVERBOSE,"Effacement du fichier %s",fic)

            os.remove(fic)

        # Fetch de la liste des nouveaux bulletins dans le répertoire
        self.bulletinsAEffacer = self.unBulletinManager.getListeFichiers(self.unBulletinManager.getPathSource(),[])

        self.logger.writeLog(self.logger.VERYVERYVERBOSE,"Liste des fichiers lus : %s",str(self.bulletinsAEffacer))

        # Lecture de ces bulletins et stockage dans une liste
        mapData = self.unBulletinManager.getMapBulletinsBruts(self.bulletinsAEffacer)

        # Ici on s'intéresse seulement au bulletins bruts, extraction du bulletin d'à partir du map
        data = [ mapData[x] for x in mapData ]

        self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins lus",len(data))

        # Dans tous les cas, écrire les collection s'il y a lieu
        self.unCollectionManager.writeCollection()

        return data

    def write(self,data):
        __doc__ =  gateway.gateway.write.__doc__ + \
        """### Ajout de collectionGateway ###

           Collection s'il y a lieu, sinon écriture par un bulletinManager ordinaire.

           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """

        self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins seront écrits",len(data))

        while True:
            if len(data) <= 0:
                break

            rawBulletin = data.pop(0)

            # Si le bulletin doit etre collecté
            if self.unCollectionManager.needsToBeCollected(rawBulletin):

                # Envoi dans collManager
                self.unCollectionManager.addBulletin(rawBulletin,)

            else:
                # Parcours normal (non collecté)
                self.logger.writeLog(self.logger.DEBUG, "RAW BULLETIN: %s" % rawBulletin) #DL20050428
                self.logger.writeLog(self.logger.DEBUG, "Don't need to be collected => bulletinManager treatment") #DL20050428
                self.unBulletinManager.writeBulletinToDisk(rawBulletin,compteur=True,includeError=True)

        # Dans tous les cas, écrire les collection s'il y a lieu
        self.unCollectionManager.writeCollection()


    def shutdown(self):
        __doc__ = gateway.gateway.shutdown.__doc__
        gateway.gateway.shutdown(self)

        self.unCollectionManager.close()

    def reloadConfig(self):
        __doc__ = gateway.gateway.reloadConfig.__doc__
        self.logger.writeLog(self.logger.INFO,'Demande de rechargement de configuration')

        try:

            newConfig = gateway.gateway.loadConfig(self.pathToConfigFile)

            ficCircuits = newConfig.ficCircuits
            ficCollection = newConfig.ficCollection
            collectionParams = newConfig.collectionParams

            # Reload du fichier de circuits
            # -----------------------------
            self.unCollectionManager.reloadMapCircuit(ficCircuits)

            # Partage du même map pour les 2 managers
            self.unBulletinManager.setMapCircuits(self.unCollectionManager.getMapCircuits())

            self.options.ficCircuits = ficCircuits

            # Reload du fichier de stations
            # -----------------------------
            self.unCollectionManager.reloadMapEntetes(ficCollection)

            self.options.ficCollection = ficCollection

            # Reload des paramètres de la collection
            # --------------------------------------
            self.logger.writeLog(self.logger.INFO,'Rechargement des paramètres de la collection')

            self.unCollectionManager.setCollectionParams(collectionParams)

            self.logger.writeLog(self.logger.INFO,'Succès du rechargement de la config')

        except Exception, e:

            self.logger.writeLog(self.logger.ERROR,'Échec du rechargement de la config!')

            self.logger.writeLog(self.logger.DEBUG,"Erreur: %s", str(e.args))
