
import gateway
import socketManagerAMIS
import bulletinManagerAMIS
from socketManager import socketManagerException

class senderAMIS(gateway.gateway):
    __doc__ = gateway.gateway.__doc__ + \
    """
    #### CLASSE senderAMIS ####

    Nom:
    senderAMIS

    Paquetage:

    Statut:
    Classe concrete

    Responsabilites:
    -Lire des bulletins en format AMIS;
    -Envoyer les bulletins AMIS lus selon un ordre de priorite dans une arborescence;
    -Communiquer en respectant le standard "Async Over TCP".

    Attributs:
    Attribut de la classe parent gateway

    Methodes:
    Methodes de la classe parent gateway

    Auteur:
    Pierre Michaud

    Date:
    2004-10-15
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
        Instancie un objet senderAMIS.

        Auteur:
        Pierre Michaud

        Date:
        Octobre 2004
        """
        gateway.gateway.__init__(self,path,options,logger)
        self.establishConnection()

        # Instanciation du bulletinManagerAMIS selon les arguments issues du fichier
        # de configuration
        self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAMIS")
        #self.unBulletinManagerAMIS = \
        #        bulletinManagerAMIS.bulletinManagerAMIS(self.config.pathTemp,logger,...)

    def shutdown(self):
        __doc__ = gateway.gateway.shutdown.__doc__ + \
        """
        ### senderAMIS ###
        Nom:
        shutdown

        Parametres d'entree:
        -Aucun

        Parametres de sortie:
        -Aucun

        Description:
        Termine proprement l'existence d'un senderAMIS.  Les taches en cours sont terminees
        avant d'eliminer le senderAMIS.

        Nom:
        Pierre Michaud

        Date:
        Octobre 2004
        """
        gateway.gateway.shutdown(self)

        resteDuBuffer, nbBullEnv = self.unSocketManagerAMIS.closeProperly()

        self.write(resteDuBuffer)

        self.logger.writeLog(self.logger.INFO,"Le senderAMIS est mort.  Traitement en cours reussi.")

    def establishConnection(self):
        __doc__ = gateway.gateway.establishConnection.__doc__ + \
        """
        ### senderAMIS ###
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
        Octobre 2004
        """

        # Instanciation du socketManagerAMIS
        self.logger.writeLog(self.logger.DEBUG,"Instanciation du socketManagerAMIS")
        self.unSocketManagerAMIS = \
                        socketManagerAMIS.socketManagerAMIS(self.logger,type='master', \
                                                        localPort=self.config.localPort,\
                                                        remoteHost=self.config.remoteHost,
                                                        timeout=self.config.timeout)

    def read(self):
        __doc__ =  gateway.gateway.read.__doc__ + \
        """
        ### senderAMIS ###
        Nom:
        read

        Parametres d'entree:
        -Aucun

        Parametres de sortie:
        -data: les donnees lues

        Description:
        Lit les bulletins contenus dans un repertoire.  Le repertoire
        contient les bulletins de la priorite courante.

        Nom:
        Pierre Michaud

        Date:
        Octobre 2004
        """
        data = []
        data = ['The curse it lives on in their eyes','asdf']
        return data

 #               while True: #FIXME necessaire pour ce read????
                #FIXME
#                       try:
#                               priorite = self.unBulletinManagerAMIS.ordonnancer()
#                               data = self.unBulletinManager.readBulletin(priorite)
#                       except bulletinManagerException, e:
#                               JE SUIS ICI!!!!!!!!!!!!!!!
#A REFAIRESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSZE
    def write(self,dato):

        self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins sont envoyes",len(dato))

        while True:
            if len(dato) <= 0:
                break

            rawBulletin = dato.pop(0)

            # FIXME test ici si une erreur
            #self.unBulletinManagerAMIS.writeBulletinToDisk(rawBulletin)
            self.unSocketManagerAMIS.sendBulletin(rawBulletin)
