# -*- coding: UTF-8 -*-
"""ReceiverAm: socketAm -> disk, incluant traitement pour les bulletins"""

import gateway
import socketManagerAm
import bulletinManagerAm
import socketManager
from socketManager import socketManagerException
import fet

class receiverAm(gateway.gateway):
    __doc__ = gateway.gateway.__doc__ + \
    """
    ### Ajout de receiver AM ###

    Implantation du receiver pour un feed AM. Il est constitué
    d'un socket manager AM et d'un bulletin manager AM.

    Auteur: Louis-Philippe Thériault
    Date:   Octobre 2004
    """

    def __init__(self,path,options,logger):
        gateway.gateway.__init__(self,path,options,logger)

        self.establishConnection()

        self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAm")
        
        self.pathFichierStations = fet.FET_ETC + 'collection_stations.conf'

        # Instanciation du bulletinManagerAm avec la panoplie d'arguments.
        self.unBulletinManager = \
            bulletinManagerAm.bulletinManagerAm(
                fet.FET_DATA + fet.FET_RX + options.source, logger, \
                pathDest = '/apps/pds/RAW/-PRIORITY', \
                pathFichierCircuit = '/dev/null', \
                SMHeaderFormat = options.AddSMHeader, \
                pathFichierStations = self.pathFichierStations, \
                extension = options.extension, \
                mapEnteteDelai = options.mapEnteteDelai,
                use_pds = self.options.use_pds )



    def shutdown(self):
        __doc__ = gateway.gateway.shutdown.__doc__ + \
        """### Ajout de receiverAm ###

           Fermeture du socket et finalisation du traîtement du
           buffer.

           Utilisation:

                Fermeture propre du programme via sigkill/sigterm

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Octobre 2004
        """
        gateway.gateway.shutdown(self)

        if self.unSocketManagerAm.isConnected():
            resteDuBuffer, nbBullEnv = self.unSocketManagerAm.closeProperly()

            self.write(resteDuBuffer)

        self.logger.writeLog(self.logger.INFO,"Succès du traîtement du reste de l'info")

    def establishConnection(self):
        __doc__ = gateway.gateway.establishConnection.__doc__ + \
        """### Ajout de receiverAm ###

           establishConnection ne fait que initialiser la connection
           socket.

           Utilisation:

                En encapsulant la connection réseau par cette méthode, il est plus
                facile de gérer la perte d'une connection et sa reconnection.

           Visibilité:  Privée
           Auteur:      Louis-Philippe Thériault
           Date:        Octobre 2004
        """

        self.logger.writeLog(self.logger.DEBUG,"Instanciation du socketManagerAm")

        # Instanciation du socketManagerAm
        self.unSocketManagerAm = \
                socketManagerAm.socketManagerAm(self.logger,type='slave', \
                        port=self.options.port)

    def read(self):
        __doc__ =  gateway.gateway.read.__doc__ + \
        """### Ajout de receiverAm ###

           Le lecteur est le socket tcp, géré par socketManagerAm.

           Visibilité:  Privée
           Auteur:      Louis-Philippe Thériault
           Date:        Octobre 2004


           Modification le 25 janvier 2005: getNextBulletins()
           retourne une liste de bulletins.

           Auteur:      Louis-Philippe Thériault
        """
        if self.unSocketManagerAm.isConnected():
            try:
                data = self.unSocketManagerAm.getNextBulletins()
            except socketManager.socketManagerException, e:
                if e.args[0] == "la connexion est brisee":
                    self.logger.writeLog(self.logger.ERROR,"Perte de connection, traîtement du reste du buffer")
                    data, nbBullEnv = self.unSocketManagerAm.closeProperly()
                else:
                    raise
        else:
            raise gateway.gatewayException("Le lecteur ne peut être accédé")

        self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins lus",len(data))

        return data

    def write(self,data):
        __doc__ =  gateway.gateway.write.__doc__ + \
        """### Ajout de receiverAm ###

           L'écrivain est un bulletinManagerAm.

           Visibilité:  Privée
           Auteur:      Louis-Philippe Thériault
           Date:        Octobre 2004
        """

        self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins seront écrits",len(data))

        while True:
            if len(data) <= 0:
                break

            rawBulletin = data.pop(0)

            self.unBulletinManager.writeBulletinToDisk(rawBulletin,includeError=True)

    def reloadConfig(self):
        __doc__ = gateway.gateway.reloadConfig.__doc__
        self.logger.writeLog(self.logger.INFO,'Demande de rechargement de configuration')

        try:

            newConfig = gateway.gateway.loadConfig(self.pathToConfigFile)

            ficCircuits = newConfig.ficCircuits
            ficCollection = newConfig.ficCollection

            # Reload du fichier de circuits
            # -----------------------------
            self.unBulletinManager.reloadMapCircuit(ficCircuits)

            self.config.ficCircuits = ficCircuits

            # Reload du fichier de stations
            # -----------------------------
            self.unBulletinManager.reloadMapEntetes(ficCollection)

            self.config.ficCollection = ficCollection

            self.logger.writeLog(self.logger.INFO,'Succès du rechargement de la config')

        except Exception, e:

            self.logger.writeLog(self.logger.ERROR,'Échec du rechargement de la config!')

            self.logger.writeLog(self.logger.DEBUG,"Erreur: %s", str(e.args))
