# -*- coding: UTF-8 -*-
"""Gestionnaire de bulletins

   Auteur:      Louis-Philippe Thériault
   Date:        Octobre 2004
"""
import math, string, os, bulletinPlain, traceback, sys, time, fet

__version__ = '2.0'

class bulletinManagerException(Exception):
    """Classe d'exception spécialisés relatives au bulletin managers"""
    pass

class bulletinManager:
    """Gestionnaire de bulletins général. S'occupe de la manipulation
       des bulletins en tant qu'entités, mais ne fait pas de traîtements
       à l'intérieur des bulletins.

       pathTemp             path

                            - Obligatoire, doit être sur le même file system que
                              pathSource/pathDest

       pathSource           path

                            Répertoire d´ou les fichiers sont lus.

       pathDest             path
                            Répertoire ou les fichiers sont écrits.
                            en mode use_pds pathDest est necessaire.
                            Si le manager ne fait qu'écrire les fichier sur le disque,
                            seul pathDest est nécessaire.
                            en mode fet, le fichier va etre directement ingéré

       mapEnteteDelai       map

                            - Gestion pour la validité des fichiers concernant les délais.

                            - Map d'entêtes pointant sur des tuples, avec comme champ [0] le nombre de minutes
                              avant, et champ [1] le nombre de minutes après, pour que le bulletin soit valide.

                            Nb: Mettre à None pour désactiver la fonction de validité des fichiers
                                concernant les délais.

                            Ex: mapEnteteDelai = { 'CA':(5,20),'WO':(20,40)}

       SMHeaderFormat       Bool

                            - Ajout du champ "AAXX jjhh4\\n" aux bulletins SM/SI.

       ficCollection        path

                            - Path vers le fichier de collection correctement formatte
                              Doit etre mis a None si on veut garder les bulletins
                              intouchés.

                            Nb: Mettre a None pour desactiver cette fonction

       pathFichierCircuit   path

                            - Remplace le -CIRCUIT dans l'extension par la liste de circuits
                              séparés par un point.

                            Nb: Mettre a None pour desactiver cette fonction

       maxCompteur          Int

                            - Compteur à ajouter à la fin des fichiers (dans le nom du fichier)

       Un bulletin manager est en charge de la lecture et écriture des
       bulletins sur le disque.

    """

    def __init__(self,
            pathTemp,
            logger,
            pathSource=None,
            pathDest=None,
            maxCompteur=99999, \
            lineSeparator='\n',
            extension=':',
            pathFichierCircuit=None,
            mapEnteteDelai=None,
            use_pds=0):

        self.logger = logger
        self.pathSource = self.__normalizePath(pathSource)
        self.pathDest = self.__normalizePath(pathDest)
        self.pathTemp = self.__normalizePath(pathTemp)
        self.maxCompteur = maxCompteur
        # FIXME: this should be read from a config file, haven't understood enough yet.
        self.use_pds = use_pds
        self.compteur = 0
        self.extension = extension
        self.lineSeparator = lineSeparator
        self.mapEnteteDelai = mapEnteteDelai

        #map du contenu de bulletins en format brut
        #associe a leur arborescence absolue
        self.mapBulletinsBruts = {}

        # Init du map des circuits
        self.initMapCircuit(pathFichierCircuit)


    def effacerFichier(self,nomFichier):
        try:
            os.remove(nomFichier)
        except:
            self.logger.writeLog(self.logger.ERROR,"(BulletinManager.effacerFichier(): Erreur d'effacement d'un bulletin)")
            raise

    def writeBulletinToDisk(self,unRawBulletin,compteur=True,includeError=True):
        """writeBulletinToDisk(bulletin [,compteur,includeError])

           unRawBulletin        String

                                - Le unRawBulletin est un string, et il est instancié
                                  en bulletin avane l'écriture sur le disque
                                - Les modifications sont effectuées via
                                  unObjetBulletin.doSpecificProcessing() avant
                                  l'écriture

           compteur             Bool

                                - Si à True, le compteur est inclut dans le nom du fichier

           includeError         Bool

                                - Si à True et que le bulletin est erronné, le message
                                  d'erreur est inséré au début du bulletin

           Utilisation:

                   Écrit le bulletin sur le disque. Le bulletin est une simple string.

        """

        if self.pathDest == None:
            raise bulletinManagerException("opération impossible, pathDest n'est pas fourni")

        if self.compteur > self.maxCompteur:
            self.compteur = 0

        self.compteur += 1

        unBulletin = self.__generateBulletin(unRawBulletin)
        unBulletin.doSpecificProcessing()

        # Vérification du temps d'arrivée
        self.verifyDelay(unBulletin)

        # Génération du nom du fichier
        nomFichier = self.getFileName(unBulletin,compteur=compteur)
        if not self.use_pds:
            nomFichier = nomFichier + ':' + time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) )

        tempNom = self.pathTemp + nomFichier
        try:
            unFichier = os.open( tempNom , os.O_CREAT | os.O_WRONLY )

        except (OSError,TypeError), e:
            # Le nom du fichier est invalide, génération d'un nouveau nom

            self.logger.writeLog(self.logger.WARNING,"Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
            self.logger.writeLog(self.logger.EXCEPTION,"Exception: " + ''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))

            nomFichier = self.getFileName(unBulletin,error=True,compteur=compteur)
            tempNom = self.pathTemp + nomFichier
            unFichier = os.open( tempNom, os.O_CREAT | os.O_WRONLY )

        os.write( unFichier , unBulletin.getBulletin(includeError=includeError) )
        os.close( unFichier )
        os.chmod(tempNom,0644)

        if self.use_pds:
            pathDest = self.getFinalPath(unBulletin)

            if not os.access(pathDest,os.F_OK):
                os.mkdir(pathDest, 0755)

            os.rename( tempNom , pathDest + nomFichier )
            self.logger.writeLog(self.logger.INFO, "Ecriture du fichier <%s>",pathDest + nomFichier)
        else:
            entete = ' '.join(unBulletin.getHeader().split()[:2])

            if self.mapCircuits.has_key(entete):
                clist = self.mapCircuits[entete]['routing_groups']
            else:
                clist = []

            fet.directIngest( nomFichier, clist, tempNom, self.logger )
            os.unlink(tempNom)



    def __generateBulletin(self,rawBulletin):
        """__generateBulletin(rawBulletin) -> objetBulletin

           Retourne un objetBulletin d'à partir d'un bulletin
           "brut".

        """
        return bulletinPlain.bulletinPlain(rawBulletin,self.logger,self.lineSeparator)

    def readBulletinFromDisk(self,listeRepertoires,listeFichiersDejaChoisis=[],priorite=False):
        """
        Nom:
        readBulletinFromDisk

        Parametres d'entree:
        -listeRepertoires:
                les repertoires susceptibles d'etre lus,
                en format absolu
        -listeFichiersDejaChoisis (optionnel):
                les fichiers choisis lors du
                precedent appel, en format absolu
        -priorite (optionnel):
                si priorite = 1 ou True, la methode ordonnancer()
                est executee

        Parametres de sortie:
        -mapBulletinsBruts:
                dictionnaire du contenu brut des bulletins lus associe
                a leur arborescence absolue

        Description:
        Lit le contenu des fichiers contenus dans le repertoire
        voulu et retourne des bulletins bruts, ainsi que leur
        origine absolue.  Si besoin est, un ordonnancement est effectue
        pour choisir un repertoire prioritaire, de meme qu'une validation
        des fichiers a lire en fonction de ceux deja lus.

        Auteur:
        Pierre Michaud

        Date:
        Novembre 2004
        """

        try:
                #par defaut, le premier repertoire est choisi
            repertoireChoisi = listeRepertoires[0]

            #determination du repertoire a lire
            if priorite:
                repertoireChoisi = self.ordonnancer(listeRepertoires)

            #determination des fichiers a lire
            listeFichiers = self.getListeFichiers(repertoireChoisi,listeFichiersDejaChoisis)

            #lecture du contenu des fichiers et
            #chargement de leur contenu
            map = self.getMapBulletinsBruts(listeFichiers)

            #return self.getMapBulletinsBruts(listeFichiers)
            return map

        except Exception, e:
            self.logger.writeLog(self.logger.ERROR,"bulletinManager.readBulletinFromDisk: Erreur de chargement des bulletins: %s",str(e.args))
            raise

    def getMapBulletinsBruts(self,listeFichiers):
        """
        Nom:
        getMapBulletinsBruts

        Parametres d'entree:
        -listeFichiers:
                les fichiers a lire
                en format absolu

        Parametres de sortie:
        -mapBulletinsBruts:
                dictionnaire du contenu brut des bulletins lus associe
                a leur arborescence absolue

        Description:
        Lit le contenu des fichiers contenus dans le repertoire
        voulu et retourne des bulletins bruts, ainsi que leur
        origine absolue.

        Auteur:
        Pierre Michaud

        Date:
        Novembre 2004
        """

        try:
            #vidange du map de l'etat precedent
            self.mapBulletinsBruts = {}
            #lecture et mapping du contenu brut des fichiers
            for fichier in listeFichiers:
                if os.access(fichier,os.F_OK|os.R_OK) !=1:
                    raise bulletinManagerException("Fichier inexistant: " + fichier)
                fic = open(fichier,'r')
                rawBulletin = fic.read()
                fic.close()
                self.mapBulletinsBruts[fichier]=rawBulletin

            return self.mapBulletinsBruts

        except Exception, e:
            self.logger.writeLog(self.logger.ERROR,"bulletinManager.getMapBulletinsBruts(): Erreur de lecture des bulletins: %s",str(e.args))
            raise

    def getListeFichiers(self,repertoire,listeFichiersDejaChoisis):
        """
        Nom:
        getListeFichiers

        Parametres d'entree:
        -repertoire:
                le repertoire a consulter
                en format absolu
        -listeFichiersDejaChoisis:
                les fichiers choisis lors du
                precedent appel en format absolu

        Parametres de sortie:
        -listeFichiersChoisis:
                liste des fichiers choisis

        Description:
        Lit les bulletins contenus dans un repertoire choisi selon la priorite
        courante.  Le repertoire contient les bulletins de la priorite courante.
        Les fichiers deja lus ne sont pas relus, ils sont mis de cote.

        Auteur:
        Pierre Michaud

        Date:
        Novembre 2004
        """
        try:
            #lecture du contenu du repertoire
            listeFichiers = os.listdir(repertoire)

            #transformation en format absolu
            liste = []
            for fichier in listeFichiers:
            #seuls les fichiers avec les bonnes
            #permissions sont conserves
                if fichier[0] == '.':
                    continue
                data = repertoire+'/'+fichier
                liste.append(data)

            #listeFichiers = liste

            #Retrait des fichiers deja choisis
            listeFichiersChoisis = []
            listeFichiersChoisis = [fichier for fichier in liste if fichier not in listeFichiersDejaChoisis]

            return listeFichiersChoisis

        except Exception, e:
            self.logger.writeLog(self.logger.ERROR,"bulletinManager.getListeFichiers(): Liste des repertoires invalide: %s",str(e.args))
            return 1

    def ordonnancer(self,listeRepertoires):
        """
        Nom:
        ordonnancer

        Parametres d'entree:
        -listeRepertoires:      les repertoires susceptibles d'etre lus,
                                en format absolu

        Parametres de sortie:
        -repertoireChoisi: repertoire contenant les bulletins a lire
                        selon la priorite courante, en format absolu

        Description:
        Determine, parmi une liste de repertoires, lequel
        doit etre consulte pour obtenir les bulletins prioritaires.
        Dans la classe de base, la methode ne fait que retourner le
        premier repertoire de la liste passee en parametre.  Donc,
        cette methode doit etre redefinie dans les classes derivees.

        Auteur:
        Pierre Michaud

        Date:
        Novembre 2004
        """
        try:
            sourceChoisie = listeRepertoires[0]
            return sourceChoisie

        except:
            self.logger.writeLog(self.logger.ERROR,"(Liste de repertoires invalide)")

    def getListeNomsFichiersAbsolus(self):
        return self.mapBulletinsBruts.keys()

    def __normalizePath(self,path):
        """normalizePath(path) -> path

           Retourne un path avec un '/' à la fin
        """

        if path != None:
            if path != '' and path[-1] != '/':
                path = path + '/'

        return path

    def getFileName(self,bulletin,error=False, compteur=True):
        """getFileName(bulletin[,error, compteur]) -> fileName

           Retourne le nom du fichier pour le bulletin. Si error
           est à True, c'est que le bulletin a tenté d'être écrit
           et qu'il y a des caractère "illégaux" dans le nom,
           un nom de fichier "safe" est retourné. Si le bulletin semble être
           correct mais que le nom du fichier ne peut être généré,
           les champs sont mis à ERROR dans l'extension.

           Si compteur est à False, le compteur n'est pas inséré
           dans le nom de fichier.

           Utilisation:

                Générer le nom du fichier pour le bulletin concerné.
        """
        if compteur or bulletin.getError() != None or error:
            compteur = True
            strCompteur = ' ' + string.zfill(self.compteur, len(str(self.maxCompteur)))
        else:
            strCompteur = ''

        if bulletin.getError() == None and not error:
        # Bulletin normal
            try:
                return (bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
            except Exception, e:
            # Une erreur est détectée (probablement dans l'extension) et le nom est généré avec des erreurs

                # Si le compteur n'a pas été calculé, c'est que le bulletin était correct,
                # mais si on est ici dans le code, c'est qu'il y a eu une erreur.
                if strCompteur == '':
                    strCompteur = ' ' + string.zfill(self.compteur, len(str(self.maxCompteur)))

                self.logger.writeLog(self.logger.WARNING,e)
                return ('PROBLEM_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error=True)).replace(' ','_')
        elif bulletin.getError() != None and not error:
            self.logger.writeLog( self.logger.WARNING, "Le bulletin est erronné " + bulletin.getError()[0] )
            return ('PROBLEM_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
        else:
            self.logger.writeLog(self.logger.WARNING, "L'entête n'est pas imprimable" )
            return ('PROBLEM_BULLETIN ' + 'UNPRINTABLE HEADER' + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')

    def getExtension(self,bulletin,error=False):
        """getExtension(bulletin) -> extension

           Retourne l'extension à donner au bulletin. Si error est à True,
           les champs 'dynamiques' sont mis à 'PROBLEM'.

           -TT:         Type du bulletin (2 premieres lettres)
           -CCCC:       Origine du bulletin (2e champ dans l'entête
           -CIRCUIT:    Liste des circuits, séparés par des points,
                        précédés de la priorité.

           Exceptions possibles:
                bulletinManagerException:       Si l'extension ne peut être générée
                                                correctement et qu'il n'y avait pas
                                                d'erreur à l'origine.

           Utilisation:

                Générer la portion extension du nom du fichier.
        """
        newExtension = self.extension

        if not error and bulletin.getError() == None:
            newExtension = newExtension.replace('-TT',bulletin.getType())\
                                       .replace('-CCCC',bulletin.getOrigin())

            if self.mapCircuits != None:
            # Si les circuits sont activés
            # NB: Lève une exception si l'entête est introuvable
                newExtension = newExtension.replace('-CIRCUIT',self.getCircuitList(bulletin))

            return newExtension
        else:
            # Une erreur est détectée dans le bulletin
            newExtension = newExtension.replace('-TT','PROBLEM')\
                                       .replace('-CCCC','PROBLEM')\
                                       .replace('-CIRCUIT','PROBLEM')

            return newExtension

    def lireFicTexte(self,pathFic):
        """
           lireFicTexte(pathFic) -> liste des lignes

           pathFic:        String
                           - Chemin d'accès vers le fichier texte

           liste des lignes:       [str]
                                   - Liste des lignes du fichier texte

        Utilisation:

                Retourner les lignes d'un fichier, utile pour lire les petites
                databases dans un fichier ou les fichiers de config.
        """
        if os.access(pathFic,os.R_OK):
            f = open(pathFic,'r')
            lignes = f.readlines()
            f.close
            return lignes
        else:
            raise IOError

    def reloadMapCircuit(self,pathHeader2circuit):
        """reloadMapCircuit(pathHeader2circuit)

           pathHeader2circuit:  String
                                - Chemin d'accès vers le fichier de circuits


           Recharge le fichier de mapCircuits.

           Utilisation:

                Rechargement lors d'un SIGHUP.
        """
        oldMapCircuits = self.mapCircuits

        try:

            self.initMapCircuit(pathHeader2circuit)

            self.logger.writeLog(self.logger.INFO,"Succès du rechargement du fichier de Circuits")

        except Exception, e:

            self.mapCircuits = oldMapCircuits

            self.logger.writeLog(self.logger.WARNING,"bulletinManager.reloadMapCircuit(): Échec du rechargement du fichier de Circuits")

            raise


    def initMapCircuit(self,pathHeader2circuit):
        """initMapCircuit(pathHeader2circuit)

           pathHeader2circuit:  String
                                - Chemin d'accès vers le fichier de circuits

           Charge le fichier de header2circuit et assigne un map avec comme cle
           champs:
                'routing_groups' -- list of clients to which the messages are to be routed.
'                priority'       -- priority to assign to the message.

           FIXME: Peter a fixé le chemin a /apps/px/etc/header2circuit.conf
                donc le parametre choisi simplement si on s´en sert ou pas.
        """
        if pathHeader2circuit == None:
        # Si l'option est à OFF
            self.mapCircuits = None
            return

        self.mapCircuits = {}

        # Test d'existence du fichier
        try:
            if not self.use_pds:
                pathHeader2circuit = fet.FET_ETC + 'header2client.conf'

            fic = os.open( pathHeader2circuit, os.O_RDONLY )
        except Exception:
            raise bulletinManagerException('Impossible d\'ouvrir le fichier d\'entetes ' + pathHeader2circuit + ' (fichier inaccessible)' )

        lignes = os.read(fic,os.stat(pathHeader2circuit)[6])

        bogus=[]
        self.logger.writeLog( self.logger.INFO, "validating header2client.conf, clients:" + string.join(fet.clients.keys()) )
        for ligne in lignes.splitlines():
            uneLigneSplitee = ligne.split(':')
            ahl = uneLigneSplitee[0]
            self.mapCircuits[uneLigneSplitee[0]] = {}
            try:
                self.mapCircuits[ahl] = {}
                self.mapCircuits[ahl]['entete'] = ahl
                self.mapCircuits[ahl]['routing_groups'] = ahl
                self.mapCircuits[ahl]['priority'] = uneLigneSplitee[2]
                gs=[]
                for g in uneLigneSplitee[1].split() :
                    if g in fet.clients.keys():
                        gs = gs + [ g ]
                    else:
                        if g not in bogus:
                            bogus = bogus + [ g ]
                            self.logger.writeLog( self.logger.WARNING, "client (%s) invalide, ignorée ", g )
                self.mapCircuits[ahl]['routing_groups'] =  gs
            except IndexError:
                raise bulletinManagerException('Les champs ne concordent pas dans le fichier header2circuit',ligne)

    def getMapCircuits(self):
        """getMapCircuits() -> mapCircuits

           À utiliser pour que plusieurs instances utilisant la même
           map.
        """
        return self.mapCircuits

    def setMapCircuits(self,mapCircuits):
        """setMapCircuits(mapCircuits)

           À utiliser pour que plusieurs instances utilisant la même
           map.
        """
        self.mapCircuits = mapCircuits

    def getCircuitList(self,bulletin):
        """circuitRename(bulletin) -> Circuits

           bulletin:    Objet bulletin

           Circuits:    String
                        -Circuits formattés correctement pour êtres insérés dans l'extension

           Retourne la liste des circuits pour le bulletin précédés de la priorité, pour être inséré
           dans l'extension.

              Exceptions possibles:
                   bulletinManagerException:       Si l'entête ne peut être trouvée dans le
                                                   fichier de circuits
        """
        if self.mapCircuits == None:
            raise bulletinManagerException("Le mapCircuit n'est pas chargé")

        entete = ' '.join(bulletin.getHeader().split()[:2])

        if not self.mapCircuits.has_key(entete):
            bulletin.setError('Entete non trouvée dans fichier de circuits')
            raise bulletinManagerException('Entete non trouvée dans fichier de circuits')

        # Check ici, si ce n'est pas une liste, en faire une liste
        if not type(self.mapCircuits[entete]['routing_groups']) == list:
            self.mapCircuits[entete]['routing_groups'] = [ self.mapCircuits[entete]['routing_groups'] ]

        if self.use_pds:
            return self.mapCircuits[entete]['priority'] + '.' + '.'.join(self.mapCircuits[entete]['routing_groups']) + '.'
        else:
            return self.mapCircuits[entete]['priority']

    def getFinalPath(self,bulletin):
        """getFinalPath(bulletin) -> path

           path         String
                        - Répertoire où le fichier sera écrit

           bulletin     objet bulletin
                        - Pour aller chercher l'entête du bulletin

           Utilisation:

                Pour générer le path final où le bulletin sera écrit. Génère
                le répertoire incluant la priorité.
        """
        # Si le bulletin est erronné
        if bulletin.getError() != None:
            return self.pathDest.replace('-PRIORITY','PROBLEM')

        try:
            entete = ' '.join(bulletin.getHeader().split()[:2])
        except Exception:
            self.logger.writeLog(self.logger.ERROR,"Entête non standard, priorité impossible à déterminer(%s)",bulletin.getHeader())
            return self.pathDest.replace('-PRIORITY','PROBLEM')

        if self.mapCircuits != None:
            # Si le circuitage est activé
            if not self.mapCircuits.has_key(entete):
                    # Entête est introuvable
                self.logger.writeLog(self.logger.ERROR,"Entête introuvable, priorité impossible à déterminer")
                return self.pathDest.replace('-PRIORITY','PROBLEM')

            return self.pathDest.replace('-PRIORITY',self.mapCircuits[entete]['priority'])
        else:
            return self.pathDest.replace('-PRIORITY','NONIMPLANTE')

    def getPathSource(self):
        """getPathSource() -> Path_source

           Path_source:         String
                                -Path source que contient le manager
        """
        return self.pathSource

    def verifyDelay(self,unBulletin):
        """verifyDelay(unBulletin)

           Vérifie que le bulletin est bien dans les délais (si l'option
           de délais est activée). Flag le bulletin en erreur si le delai
           n'est pas respecté.

           Ne peut vérifier le délai que si self.mapEnteteDelai n'est
           pas à None.

           Utilisation:

                Pouvoir vérifier qu'un bulletin soit dans les délais
                acceptables.
        """
        if (self.mapEnteteDelai == None):
            return

        now = time.strftime("%d%H%M",time.localtime())

#               try:
        if True:
            bullTime = unBulletin.getHeader().split()[2]
            header = unBulletin.getHeader()

            minimum,maximum = None,None

            for k in self.mapEnteteDelai.keys():
            # Fetch de l'intervalle valide dans le map
                if k == header[:len(k)]:
                    (minimum,maximum) = self.mapEnteteDelai[k]
                    break

            if minimum == None:
            # Si le cas n'est pas défini, considéré comme correct
                return

#               except Exception:
#                       unBulletin.setError('Découpage d\'entête impossible')
#                       return

        # Détection si wrap up et correction pour le calcul
        if abs(int(now[:2]) - int(bullTime[:2])) > 10:
            if now > bullTime:
            # Si le temps présent est plus grand que le temps du bulletin
            # (donc si le bulletin est généré le mois suivant que présentement),
            # On ajoute une journée au temps présent pour faire le temps du bulletin
                bullTime = str(int(now[:2]) + 1) + bullTime[2:]
            else:
            # Contraire (...)
                now = str(int(bullTime[:2]) + 1) + now[2:]

        # Conversion en nombre de minutes
        nbMinNow = 60 * 24 * int(now[0:2]) + 60 * int(now[2:4]) + int(now[4:])
        nbMinBullTime = 60 * 24 * int(bullTime[0:2]) + 60 * int(bullTime[2:4]) + int(bullTime[4:])

        # Calcul de l'interval de validité
        if not( -1 * abs(minimum) < nbMinNow - nbMinBullTime < maximum ):
            # La différence se situe en dehors de l'intervale de validité
            self.logger.writeLog(self.logger.WARNING,"Délai en dehors des limites permises bulletin: "+unBulletin.getHeader()+', heure présente '+now)
            unBulletin.setError('Bulletin en dehors du delai permis')
