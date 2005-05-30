# -*- coding: UTF-8 -*-
"""Définition des collections de bulletins"""

import traceback, sys, bulletin, time

__version__ = '2.0'

class bulletinCollection(bulletin.bulletin):
    __doc__ = bulletin.bulletin.__doc__ + \
    """### Ajout de bulletinCollection ###

       Gestion de 'collections' de bulletins.

       header       String
                    -Entete de la collection: TTAAii CCCC JJHHMM <BBB>[autre_data_faisant_partie_de_l'entete]
                    -Le champ BBB est facultatif
                    -Facultatif (l'on doit fournir mapCollection si non fourni)

       mapCollection        Map
                            -(usage interne!)
                            -'header'=str(header)
                            -'stations'=map{'station':[str(data)]}
                            -Représentation interne de la collection

       mapStations  Map
                    - Une entree par station doit être présente dans le map,
                      et la valeur doit être égale à None

       writeTime    float
                    - Nombre de sec depuis epoch quand l'écriture du fichier
                      devra être faite
                    - Utiliser time.time()

       Notes:
            bulletinCollection masque la pluspart des méthodes d'un bulletinNormal. La
            pluspart des appels peuvent êtres réutilisés, mais les appels spécifiques
            permettent un paramétrage plus précis.

       Auteur:      Louis-Philippe Thériault
       Date:        Novembre 2004
    """

    def __init__(self,logger,mapStations,writeTime,header,lineSeparator='\n'):
        self.logger = logger
        self.lineSeparator = lineSeparator
        self.writeTime = writeTime

        # Valeurs par défaut
        self.tokenIfNoData = ' NIL='
        self.bbb = None

        # Création d'une nouvelle collection
        self.errorBulletin = None

        # Initialisation des structures pour stocker la collection
        self.mapCollection = {}
        self.mapCollection['header'] = header
        self.mapCollection['mapStations'] = mapStations.copy()

        self.logger.writeLog(self.logger.INFO,"Création d'une nouvelle collection: %s",header)
        self.logger.writeLog(self.logger.VERYVERBOSE,"writeTime de la collection: %s",time.asctime(time.gmtime(writeTime)))

    def getWriteTime(self):
        """getWriteTime() -> nb_sec

           nb_sec       float
                        - Temps (en sec depuis epoch) quand la collection devra être
                          écrite

           Utilisation:
                Pour comparer avec le temps courant (time.time()), pour l'écriture
                de la collection.

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        return self.writeTime

    def dataIsComplete(self):
        """dataIsComplete() -> True/False

           Utilisation:
                Informe si tout le data pour les stations est rentré. Si tel est le
                cas la collection devrait être écrite.

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        # Tout le data est rentré si aucun station est à None
        return not( None in [self.mapCollection['mapStations'][x] for x in self.mapCollection['mapStations']] )

    def getHeader(self):
        """getHeader() -> header

           header       : String

           Retourne l'entête du fichier de collection

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        return self.mapCollection['header']

    def setHeader(self,header):
        """setHeader(header)

           header       : String

           Assigne l'entête du fichier de collection

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        self.mapCollection['header'] = header

        self.logger.writeLog(self.logger.DEBUG,"Nouvelle entête du bulletin: %s",header)

    def getType(self):
        """getType() -> type

           type         : String

           Retourne le type (2 premieres lettres de l'entête) du bulletin (SA,FT,etc...)

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        return self.mapCollection['header'][:2]

    def getOrigin(self):
        """getOrigin() -> origine

           origine      : String

           Retourne l'origine (2e champ de l'entête) du bulletin (CWAO,etc...)

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        return self.mapCollection['header'].split(' ')[1]

    def getBulletin(self,includeError=None):
        """Utiliser self.getCollection()
        """
        return self.getCollection()

    def setBBB(self,newBBB):
        """setBBB(newBBB)

           Assigne le champ newBBB au bulletin. À être utilisé avant
           getBulletin, pour fin de compatibilité.

           Utilisation:
                Si l'on veut utiliser getBulletin(), sans passer d'arguments,
                on peut setter le champ BBB avant d'appeler getBulletin().

                L'interface par getBulletin() est donc respectée.

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        header = self.mapCollection['header']

        header = ' '.join(header.split()[:3] + [newBBB])

        self.mapCollection['header'] = header


    def setTokenIfNoData(self,tokenIfNoData):
        """setTokenIfNoData(tokenIfNoData)

           Assigne le champ tokenIfNoData au bulletin. À être utilisé avant
           getBulletin, pour fin de compatibilité.

           Utilisation:
                Si l'on veut utiliser getBulletin(), sans passer d'arguments,
                on peut setter le champ setTokenIfNoData avant d'appeler getBulletin().

                L'interface par getBulletin() est donc respectée.

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        self.tokenIfNoData = tokenIfNoData

    def getCollection(self,tokenIfNoData="self.tokenIfNoData",bbb="self.bbb"):
        """getCollection(tokenIfNoData,bbb) -> collection

           tokenIfNoData        String/None
                                - Si un élément est à None pour une des stations,
                                  au nom de la station est concaténé ce champ
                                - Si est mis à None, la station sans data associée
                                  ne sera pas comprise dans la collection

                                ex: CYUL n'a pas de data

                                    "CYUL NIL=" sera la ligne associée pour
                                    cette station

           bbb                  String/None
                                - Champ BBB qui sera retourné pour la collection

           collection           String
                                - Fichier de collection, fusionné en un bulletin

           Utilisation:

                Appel qui devrait être utilisé, permet un paramétrage direct, sinon
                on peut setter les paramètres par setBBB/setTokenIfNoData.

           Visibilité:  Publique
           Auteur:      Louis-Philipe Thériault
           Date:        Novembre 2004
        """
        # Assignement des valeurs par défaut dynamiques, on ne peut les placer dans l'entête
        if tokenIfNoData == "self.tokenIfNoData":
            tokenIfNoData = self.tokenIfNoData

        if bbb == "self.bbb":
            bbb = self.bbb
        # -----------------------------------------------------------------------------------

        coll = []

        # Extraction de l'entête
        header = self.mapCollection['header']

        # On insère/remplace le champ BBB à la fin de l'entête
        if bbb != None:
            header = ' '.join(header.split()[:3] + [bbb])

        coll.append(header)
        # Ajout du header à la collection

        # Si SI/SM: Inserer AAXX jjhh4\n
	# LP: Correction, 05/30/2005
        if header[:2] in ["SM","SI"]:
           coll.append("AAXX " + header.split()[2][0:4] + "4")

        keys = self.mapCollection['mapStations'].keys()
        keys.sort()

        for station in keys:
            if self.mapCollection['mapStations'][station] == None:
                # Il n'y a pas de data pour la station courante
                if tokenIfNoData != None:
                    coll.append(station+tokenIfNoData)

            else:
                # Ajout du data pour la station
                coll.append(self.mapCollection['mapStations'][station])

        return self.lineSeparator.join(coll) + self.lineSeparator

    def addData(self,station,data):
        """addData(station,data)

           station      String

           data         String
                        - Data associé à la station

           Notes:
                La station doit être définie dans mapStations, et si elle n'est pas
                la, une exception sera levée. Si du data était déja associé,
                il est écrasé.

           Utilisation:
                Pour l'ajout du data pour une station, l'on doit appeler
                les méthodes statiques getStation/getData, sur un bulletin
                brut, puis passer l'info à addData.

           Visibilité:  Publique
           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        if not self.mapCollection['mapStations'].has_key(station):
        # La station n'est pas définie dans le fichier de stations
            self.logger.writeLog(self.logger.WARNING,\
                    "Station inconnue (collection:%s, station:%s)" % (self.mapCollection['header'].splitlines()[0],station) )

            raise bulletin.bulletinException("Station non définie")

        if self.mapCollection['mapStations'][station] == None:
            self.mapCollection['mapStations'][station] = data
        else:
            self.logger.writeLog(self.logger.WARNING,\
                    "Du data est déja présent pour la station (collection:%s, station:%s)" % \
                    (self.mapCollection['header'].splitlines()[0],station))
            # S'il y a déja du data de présent, et que le nouveau data est
            # différent
            if self.mapCollection['mapStations'][station] != data:
                self.mapCollection['mapStations'][station] += self.lineSeparator + data

                self.logger.writeLog(self.logger.DEBUG,"Le data est différent, il sera ajouté")
            else:
                self.logger.writeLog(self.logger.DEBUG,"Le data est pareil, aucune modification")



    def getStation(rawBulletin):
        """bulletinCollection.getStation(rawBulletin) -> station

           rawBulletin          String

           station              String

           Extrait la station du bulletin brut. Une exception est levée si l'on ne sait pas
           comment extraire la station ou si le bulletin est erronné.

           Méthode statique.

           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        premiereLignePleine = ""

        # Cas special, il faut aller chercher la prochaine ligne pleine
        for ligne in rawBulletin.splitlines()[1:]:
            premiereLignePleine = ligne

            if len(premiereLignePleine) > 1 and premiereLignePleine.count('AAXX ') == 0:
                break

        # Embranchement selon les differents types de bulletins
        station = ''

        if rawBulletin.splitlines()[0][0:2] == "SA":
            if rawBulletin.splitlines()[1].split()[0] in ["METAR","LWIS"]:
                station = premiereLignePleine.split()[1]
            else:
                station = premiereLignePleine.split()[0]

        elif rawBulletin.splitlines()[0][0:2] in ["SI","SM"]:
            station =  premiereLignePleine.split()[0]

        else:
            raise bulletin.bulletinException('On ne peut extraire la station')

        if station[-1] == '=':
            station = station[:-1]

        return station

    getStation = staticmethod(getStation)

    def getData(rawBulletin):
        """bulletinCollection.getData(rawBulletin) -> data

           rawBulletin          String

           data                 String

           Extrait la portion de données du bulletin.

           Méthode statique.

           Auteur:      Louis-Philippe Thériault
           Date:        Novembre 2004
        """
        splittedBulletin = rawBulletin.splitlines()

        # On enlève la première ligne (entête)
        splittedBulletin.pop(0)

        while splittedBulletin[0] == '' or splittedBulletin[0].find('AAXX') != -1:
            splittedBulletin.pop(0)

        return '\n'.join(splittedBulletin)

    getData = staticmethod(getData)
