# -*- coding: UTF-8 -*-
import gateway
import socketManagerAm
import bulletinManagerAm
import bulletinAm
from socketManager import socketManagerException
from DiskReader import DiskReader
from MultiKeysStringSorter import MultiKeysStringSorter
import fet

class senderAm(gateway.gateway):
    __doc__ = gateway.gateway.__doc__ + \
    """
    #### CLASSE senderAm ####

    Nom:
    senderAm

    Paquetage:

    Statut:
    Classe concrete

    Responsabilites:
    -Lire des bulletins en format Am;
    -Envoyer les bulletins Am lus selon un ordre de priorite dans une arborescence;
    -Communiquer en respectant le protocole Am.

    Attributs:
    Attribut de la classe parent gateway

    Methodes:
    Methodes de la classe parent gateway

    Auteur:
    Pierre Michaud

    Date:
    Janvier 2005
    """

    def __init__(self,path,options,logger):
        """
        Nom:
        __init__

        Parametres d'entree:
        -path:  repertoire ou se trouve la configuration
        -logger:        reference a un objet log

        Parametres de sortie:
        -Aucun

        Description:
        Instancie un objet senderAm.

        Auteur:
        Pierre Michaud

        Date:
        Janvier 2005
        """
        gateway.gateway.__init__(self,path,options,logger)
        self.establishConnection()
        self.options = options

        # Instanciation du bulletinManagerAm selon les arguments issues du fichier
        # de configuration
        self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAm")
        self.unBulletinManagerAm = bulletinManagerAm.bulletinManagerAm(
                 fet.FET_DATA + fet.FET_TX + options.client, logger)
        self.options.remoteHost = options.host
        self.options.localPort = options.port
        self.options.timeout    = options.connect_timeout

        self.listeFichiersDejaChoisis = []
        self.reader = None

    def shutdown(self):
        __doc__ = gateway.gateway.shutdown.__doc__ + \
        """
        ### senderAm ###
        Nom:
        shutdown

        Parametres d'entree:
        -Aucun

        Parametres de sortie:
        -Aucun

        Description:
        Termine proprement l'existence d'un senderAm.  Les taches en cours sont terminees
        avant d'eliminer le senderAm.

        Nom:
        Pierre Michaud

        Date:
        Janvier 2005
        """
        gateway.gateway.shutdown(self)

        resteDuBuffer, nbBullEnv = self.unSocketManagerAm.closeProperly()

        self.write(resteDuBuffer)

        self.logger.writeLog(self.logger.INFO,"Le senderAm est mort.  Traitement en cours reussi.")

    def establishConnection(self):
        __doc__ = gateway.gateway.establishConnection.__doc__ + \
        """
        ### senderAm ###
        Nom:
        establishConnection

        Parametres d'entree:
        -Aucun

        Parametres de sortie:
        -Aucun

        Description:
        Initialise la connexion avec le destinataire.

        Nom:
        Pierre Michaud

        Date:
        Janvier 2005
        """

        # Instanciation du socketManagerAm
        self.logger.writeLog(self.logger.DEBUG,"Instanciation du socketManagerAm")

        self.unSocketManagerAm = \
                 socketManagerAm.socketManagerAm(
                         self.logger,type='master', \
                         port=self.options.port,\
                         remoteHost=self.options.host,
                         timeout=self.options.connect_timeout)

    def read(self):
        __doc__ =  gateway.gateway.read.__doc__ + \
        """
        ### senderAm ###
        Nom:
        read

        Parametres d'entree:
        -Aucun

        Parametres de sortie:
        -data: dictionnaire du contenu d'un fichier selon son chemin absolu

        Description:
        Lit les bulletins contenus dans un repertoire.  Le repertoire
        contient les bulletins de la priorite courante.

        Nom:
        Pierre Michaud

        Date:
        Janvier 2005
        """
        self.reader = DiskReader(
                 fet.FET_DATA + fet.FET_TX + self.options.client,
                 fet.clients[self.options.client][5],
                 True, # name validation
                 self.logger,
                 eval(self.options.sorter))
        self.reader.sort()
        return(self.reader.getFilesContent(fet.clients[self.options.client][5]))


    def write(self,data):
        __doc__ =  gateway.gateway.write.__doc__ + \
        """
        ### senderAm ###
        Nom:
        write

        Parametres d'entree:
        -data: dictionnaire du contenu d'un fichier selon son chemin absolu

        Parametres de sortie:
        -Aucun

        Description:
        Genere les bulletins en format AM issus du dictionnaire data
        et les ecrit au socket approprie.

        Nom:
        Pierre Michaud

        Date:
        Janvier 2005
        """
        self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins seront envoyes",len(data))

        for index in range(len(data)):
            try:
                rawBulletin = data[index]
                unBulletinAm = bulletinAm.bulletinAm(rawBulletin,self.logger,lineSeparator='\r\r\n')
                succes = self.unSocketManagerAm.sendBulletin(unBulletinAm)
                #si le bulletin a ete envoye correctement, le fichier est efface
                if succes:
                    self.logger.writeLog(self.logger.INFO,"bulletin %s  livré ", self.reader.sortedFiles[index])
                    self.unBulletinManagerAm.effacerFichier(self.reader.sortedFiles[index])
                    self.logger.writeLog(self.logger.DEBUG,"senderAm.write(..): Effacage de " + self.reader.sortedFiles[index])
                else:
                    self.logger.writeLog(self.logger.INFO,"bulletin %s: probleme d'envoi ", self.reader.sortedFiles[index])
            except Exception, e:
                if e==104 or e==110 or e==32 or e==107:
                    self.logger.writeLog(self.logger.ERROR,"senderAm.write(): la connexion est rompue: %s",str(e.args))
                else:
                    self.logger.writeLog(self.logger.ERROR,"senderAm.write(): erreur: %s",str(e.args))
                raise
