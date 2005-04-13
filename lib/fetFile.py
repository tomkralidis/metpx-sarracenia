#! /usr/bin/env python2
# -*- coding: iso-8859-1 -*-

"""
  File Exchange Tracker - File transfer stuff. reader & writer.
        (aka, PDS ++ )

 SPEC:
  read file names in rx directory tree according to source configuration in etc/rx
  apply a priority scheme:
        send off high critical priority messages ASAP.
       keep from low priority messages from starving.

  once file names are chosen, link them into the db, and all relevant client directories.

  2005/01/22 - Initial Version, Peter Silva
"""
import os
import os.path
import time
import sys
import stat
import signal


sys.path.insert(1,sys.path[0] + '/../lib')
sys.path.insert(1,sys.path[0] + '/../lib/importedLibs')

from optparse import OptionParser
import log
import fet

logger = {}

def ingestDir(d,s,logger):
    """
    given a single directory, read all the non-hidden entries and
    attempt to ingest them.

    if it works, remove it.
    If not, just leave it there

    pay attention to the time, and abort if it takes too long

    FIXME: Doesn't pay attention to partially written files.
       uses the PDS method (chmod), preference would be to rename.
       could use given code as is, if partial files start with . (hidden.)
    """

    numfiles=0

    logger.writeLog(logger.DEBUG, "répertoire " + d + " débute." )
    for r in os.listdir(d):
        if ( r[0] == '.' ) or ( r[0:4] == 'tmp_' ) or (r[-4:] == '.tmp' ) or not os.access(r, os.R_OK):
            continue
        i=fet.ingestName(r,s) # map reception name to ingest name
        rr=d + "/" + r
        if fet.ingest(i,rr, logger) == 1:
            logger.writeLog(logger.INFO, "fichier " + rr + " ingérée comme " + i)
            os.unlink( rr )
        else:
            logger.writeLog(logger.ERROR, "fichier " + rr + " non-ingérable " )
        numfiles = numfiles + 1

    return numfiles



def checkSource(s, sources,logger, igniter):
    """look for source directories with data to ingest. Trigger ingestion.

       Priority scheduling scheme.
          -- scan all at pri x
             if found no files at pri x, then go to x+1
             if > thresh files fount at pri x, then  go to x+1

       thresh == 100
    """

    if not os.path.exists( fet.FET_DATA + fet.FET_RX):
        logger.writeLog(logger.FATAL, "ingest queue directory does not exist" )
        return

    # initialize history array.
    dmodified = {}
    logger.writeLog(logger.INFO, "Début du programme, initialization completée")

    while(1):
        if igniter.reloadMode == True:
           fet.startup(igniter.options, igniter.logger)
           igniter.reloadMode = False
           logger.writeLog(logger.INFO, "%s has been reload" % igniter.direction)

        dname = fet.sourceQDirName(s)

        if dname == '':
            continue

        fet.createDir(dname)
        dstat=os.stat( dname );

        # if the dir has changed, then ingest.
        if not dname in dmodified.keys():
            dmodified[ dname ]= 0

        if dstat.st_mtime > dmodified[ dname ] :
            #print "New files!"
            os.chdir(dname)
            dmodified[ dname ] = dstat.st_mtime
            ingestDir( dname, s, logger )
        else:
            time.sleep(1)


#
#  File Exchange Tracker - File Transmitter
#       (aka, PDS ++ )
#
# SPEC:
#  read file names in tx directory tree according to source configuration in etc/tx
#  apply a priority scheme:
#       send off high critical priority messages ASAP.
#       keep from low priority messages from starving.
#
#

from ftplib import FTP


def sendFiles(c, files,logger):
    """ send the given list of files, in order.

        attempt to send the given list of files, logging the result

     The crappy algorithm I will use to get a demo:
        for each file, figure out where to send it, do it & logging the result.

     a much better algorithm:
        1. group the files according to similar destination. (same host,user)
        2. initiate one connection for each grouping.
        3. send them.
             for each one, either: logg success, or failure.
        4.  o

      Things to consider:
          -- exponential backup when there are connection failures.
          -- maintain a list of servers which are down, continue sending to
             those machines which are up (depends on imask matches.)
          -- do we really want to support multiple hosts as destinations
             for a single client ?  Think about multiple backoff tracking.- pitq
          -- FIXME: just gives up and tries again.
      a match looks like so...
      ['imask', '*:*:*:*:*', 'ftp://am:Pr2namPW@localhost/apps/out', 'WHATFN']
  FIXME:
      -- correct crappy algorithm.
      -- pay attention to protocol spec.

    """
    ftphost=''
    ftpdir=''
    for p in files:
        f = p[p.rfind('/')+1:]
        m = fet.clientMatch(c,f)
        if not m:
            logger.writeLog( logger.INFO, "file " + os.path.basename(f) + " removed, no matching imask" )
            os.unlink(p)
            continue
        dfn = fet.destFileName(f,m)
        #print "match is: ", m
        if dfn == '' or m[2] == 'NULL':
            logger.writeLog(logger.ERROR, "fichier " + os.path.basename(f) + " pas routable par " + c )
            continue
        else:
            (proto, dspec, uspec, pwspec, hspec, pspec) = fet.urlSplit(m[2])
            if proto == 'file':
                there = dspec + '/' + dfn
                try:
                    os.copy( p , there )
                    os.unlink( p )
                    logger.writeLog( logger.INFO, "fichier " + os.path.basename(f) + " livré à " + there )
                except:
                    (type, value, tb) = sys.exc_info()
                    logger.writeLog( logger.ERROR, "pas capable d'ecrire" + there + ": " + "type: %s, value: %s" % (type, value))
                    time.sleep(10)  # relax, buy a cherry blossom, don't be shy.
                    return #FIXME: no point to continue looping...

            elif proto == 'ftp':

                # We remove the first / (if there was only one => relative path, if there was two => absolute path)
                dspec = dspec[1:]

                # assure ourselves that the ftp object is initialized.
                if ftphost != hspec:
                    if ftphost != '':
                        ftp.quit()
                    if hspec == '':
                        logger.writeLog( logger.ERROR, "pas de host défini pour " + c + repr(m) )
                        continue

                    try:
                        ftp = FTP( hspec, uspec, pwspec )
                    except:
                        #excinfo= sys.exc_info()
                        (type, value, tb) = sys.exc_info()
                        logger.writeLog( logger.ERROR, "pas capable de me brancher à " + uspec + '@' + hspec + "(old was " + ftphost + ": " + "type: %s, value: %s" % (type, value))
                        time.sleep(10)  # relax, buy a cherry blossom, don't be shy.
                        return #FIXME: no point to continue looping...

                    ftphost=hspec
                    ftpdir=''
                if ftpdir != dspec:
                    ftp.cwd(dspec)
                    ftpdir = dspec

                #FIXME: does not take care of tmp renaming or chmod yet.
                try:
                    #FIXME: does not do the chmod thing, uses a temporary name instead.
                    pfn = open( p, 'r' )
                    tmpnam = dfn + ".tmp"
                    ftp.storbinary("STOR " + tmpnam , pfn )
                    pfn.close()
                    ftp.rename( tmpnam, dfn )
                    os.unlink( p )
                    logger.writeLog( logger.INFO, "fichier " + os.path.basename(f) + " livré à "  + \
                      proto + ":" + hspec + " " + dspec + " " + dfn )
                except:
                    (type, value, tb) = sys.exc_info()
                    logger.writeLog( logger.ERROR, "pas capable d'écrire le fichier " + os.path.basename(p) + " à "  + proto + ":" + hspec + " " + dspec + " " + dfn + ": " + "type: %s, value: %s" % (type, value))
                    try:
                        ftp.quit()
                    except:
                        (type, value, tb) = sys.exc_info()
                        logger.writeLog( logger.ERROR, "ftq.quit() problem! " + "Type: %s, Value: %s" % (type, value))

                    time.sleep(10) # see cherry blossom above.
                    return


            else:
                logger.writeLog( logger.INFO, "protocol " + proto + " pas encore implanté. Ça te tentera de t´y mettre?" )


    if ftphost != '':
        ftp.quit()


def checkDir(d,logger):
    """
    given a single directory, read all the non-hidden entries and
    attempt to ingest them.

    if it works, remove it.
    If not, just leave it there

    """

    dirfiles=[]

    for t in os.listdir(d):
        p=os.path.join(d,t)

        if ( t[0] == '.' ) or ( t[0:4] == 'tmp_' ) or (t[-4:] == '.tmp' ) or not os.access(p, os.R_OK):
            continue
        dirfiles = dirfiles + [ p ]

    return dirfiles


logger = {}
dmodified = {}

def doClient(c,howtoprioritize,logger):
    """ process the files queued for a single client.

        look at all the subdirectories in the client queue
        sort all the files using 'howtoprioritize'.
        send them.
    """
    global dmodified

    cname = fet.FET_DATA + fet.FET_TX + c
    cfiles = []

    for t in os.listdir( cname ):

        dname=os.path.join(cname,t)

        if ( t[0] == '.' ) or ( t[0:4] == 'tmp_' ) or (t[-4:] == '.tmp' ) or not os.access(dname, os.R_OK):
            continue

        # if the dir has changed, then ingest.
        try:
            dstat=os.stat(dname) ;
        except:
            logger.writeLog( logger.WARNING, "stat failed for " + dname )
            continue

        if not stat.S_ISDIR(dstat[stat.ST_MODE]):
            cfiles = cfiles + [ dname ]
            continue

        if not dname in dmodified.keys():
            dmodified[ dname ] = 0

        if (dstat.st_mtime+2) >= dmodified[ dname ] :
            dmodified[ dname ] = dstat.st_mtime
            cfiles= cfiles + checkDir( dname, logger )

    if cfiles:
        cfiles.sort(howtoprioritize)
        sendFiles( c, cfiles, logger )
    else:
        fet.pushWorkList(logger)
    time.sleep(1) # this sleep is absolutely critical... avoids deadlock conditions with mtime,


def checkClient( c, clients, howtoprioritize, logger ):
    """look for client directories with data to transmit. Trigger ingestion.

       Priority scheduling scheme.
          -- scan all at pri x
             if found no files at pri x, then go to x+1
             if > thresh files fount at pri x, then  go to x+1

       thresh == 100
  FIXME holdover from rx
    """


    if not os.path.exists( fet.FET_DATA + fet.FET_TX):
        logger.writeLog(logger.FATAL, "client queues parent directory" + fet.FET_DATA+ fet.FET_TX + " does not exist" )
        return


    while(1):
        doClient(c,howtoprioritize,logger)


def filePrio( x, y ):
    """ comparator function for sort.

        based on criteria (fields 4 and 6 are the priority and timestamp,
        respectively.  )
    """
    xx = os.path.basename(x).split(':')
    yy = os.path.basename(y).split(':')
    return cmp ( xx[4] + xx[6], yy[4] + yy[6] )

#checkClient( sys.argv[1], fet.clients, filePrio, logger )
