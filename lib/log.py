# -*- coding: UTF-8 -*-
"""Système efficace pour le logging"""

# Gestion de paths relatifs, si l'on veut importer le module seul
pathDeLaLibrairie = '/'.join(__file__.split('/')[:-1])

if not '/' in pathDeLaLibrairie:
    pathDeLaLibrairie = '.'

import sys
sys.path.insert(1,pathDeLaLibrairie + '/../lib/importedLibs/')

import logging, logging.handlers

class log:
    """Classe pour le log.

       Pour inscrire un message au log, il suffit d'appeler
       writeLog.

       Pour l'instanciation:

            filename:       path
                            -Chemin de destination pour le log

            debug:          booléen
                            -Si à True, 2 logs sont créés, dont 1
                             qui est "very verbose"

       Auteur:      Louis-Philippe Thériault
       Date:        Octobre 2004
    """

    def __init__(self,filename,debug=True):
        self.debug = debug

        # Init du handler et du formatter pour le log normal
        unTimedRotatingFileHandler = logging.handlers.TimedRotatingFileHandler(filename, when='midnight', interval=1, backupCount=5)
        unFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s","%x %X")
        unTimedRotatingFileHandler.setFormatter(unFormatter)

        # Création des loggers
        self.log = logging.Logger('root')

        # Ajout des handlers
        self.log.addHandler(unTimedRotatingFileHandler)

        # Ajout des niveaux de loggers
        self.log.setLevel(logging.INFO)

        if self.debug:
            # Init du handler et du formatter pour le log debug
            unTimedRotatingFileHandlerDebug = logging.handlers.TimedRotatingFileHandler(filename+'_debug', when='midnight', interval=1, backupCount=5)
            unTimedRotatingFileHandlerDebug.setFormatter(unFormatter)

            self.logDebug = logging.Logger("Debug")
            self.logDebug.addHandler(unTimedRotatingFileHandlerDebug)
            self.logDebug.setLevel(3)

        self.CRITICAL = logging.CRITICAL
        self.ERROR = logging.ERROR
        self.DEBUG = logging.DEBUG
        self.FATAL = logging.FATAL
        self.WARNING = logging.WARNING
        self.INFO = logging.INFO
        self.EXCEPTION = logging.ERROR
        self.VERYVERBOSE = 5            # Niveau de logging 5
        self.VERYVERYVERBOSE = 3

        # Setting du nom pour les niveaux "custom"
        logging.addLevelName(self.VERYVERBOSE,'VERYVERBOSE')
        logging.addLevelName(self.VERYVERYVERBOSE,'VERYVERYVERBOSE')

    def writeLog(self, level, msg, *args, **kwargs):
        """writeLog(level,msg[,args])

           level:       Attributs de la classe log
                        -Valeurs possibles:
                                (CRITICAL,ERROR,DEBUG,
                                 FATAL,WARNING,INFO,
                                 EXCEPTION,VERYVERBOSE)
                        -ERROR et EXCEPTION sont la
                         même chose

           msg:         String
                        -Message à inscrire dans le log

           args:        Arguments séparés par une virgule
                        -Même système de "remplacement" de
                         variables que les string en C.
                         ex: %s remplacé par une string,
                             %d remplacé par un décimal

           L'on peut soir bâtir le message par concaténation (méthode
           standard dans python) ou le remplacement de tokens en C.

          Visibilité:   Publique
          Auteur:       Louis-Philippe Thériault
          Date:         Octobre 2004
        """
        self.log.log(level, msg, *args, **kwargs)

        if self.debug:
            self.logDebug.log(level, msg, *args, **kwargs)
