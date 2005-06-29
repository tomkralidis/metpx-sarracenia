#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""

  File Exchange Tracker

  flow:
        -- open directory, read name, create DB entry, link DB
          entry to client dirs.  Do the above in a manner similar to PDS.

       -- if we do the delivery thing, then base it on curl (pycurl?) robust
          functionality for Command line URL's does get & put with retries.


  Inputs:
                -- ingest directory       ingestdir
                -- source configurations
                -- client configurations  clientconfigs

        my LISP is showing...

        The data structures are two lists, one of sources, the other of clients.
        sources are read in from /apps/px/etc/rx/*.conf,

        The client configs are read from /apps/px/etc/tx/*.conf


 2005/01/10 - begun by Peter Silva

"""

import re
import fnmatch
import copy
import os
import time
import string
import sys
import signal
import log
from optparse import OptionParser


#FET_DATA='/apps/px/'
#FET_DATA='/tmp/fet/'
FET_DATA='/apps/px/'
FET_DB= 'db/today/'

FET_TX= 'txq/'
FET_RX= 'rxq/'
FET_CL= 'clq/'
FET_TMP= 'tmp/'

FET_ETC='/apps/px/etc/'

#FET_ETC='../etc/'

options={}

#
# These URL routines are extremely stupid.
#    -- there is a module called urlparse, which does most of the same job.
#       FIXME: these routine should #1 be separated into another module, and:
#              #2 use python urlparse and just do the rest.
#              could reduce size of routines considerably

def isTrue(s):
    if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
        s == 'Yes' or s == 'YES' or s == 'TRUE' or s == 'ON' or \
        s == '1' or  s == 'On' :
        return True
    else:
        return False


def urlSplit(url):

    protocol=''
    host=''
    port=''
    user=''
    password=''
    dirspec=''

    if len(url)== 0:
        return [ protocol, dirspec, user, password, host, port ]

    delim = url.find(':')
    protocol = url[0:delim]
    if protocol == 'file':
        rest = url[delim+1:]
        if len(rest) == 0:
            return [ protocol, dirspec, user, password, host, port ]

    else:
        rest = url[delim+3:]

    if rest[0] == '/':
        dirspec = rest
    else:
        delim = string.find(rest,'/')
        if delim > 0:
            dirspec= rest[delim:]
            rest = rest[0:delim]
        else:
            dirspec=''

        delim = string.find(rest,'@')
        if delim > 0 :
            host = rest[delim+1:]
            rest = rest[0:delim]
            delim = string.find(host, ':' )
            if delim > 0:
                port = host[delim+1:]
                host = host[0:delim]

            delim = string.find(rest, ':')
            if delim > 0 :
                user = rest[:delim]
                password = rest[delim+1:]
            else:
                user=rest
        else:
            delim = string.find(rest, ':')
            if delim > 0:
                host = rest[:delim]
                port = rest[delim+1:]
            else:
                host=rest

    #print "urlSplit proto="+ protocol +" dir="+ dirspec +' u='+ user +' pw='+ password +' h='+ host  +' port='+ port
    return [ protocol, dirspec, user, password, host, port ]


def urlJoin( protocol, destdir, user, pw, host, port ):

#  print "urlJoin proto="+ protocol +" dir="+ destdir +' u='+ user +' pw='+ pw +' h='+ host  +' p='+ port
    if protocol == 'file':
        it = protocol + ':'
    else:
        it = protocol + '://'
        if user != '':
            it = it + user
            if pw != '':
                it = it + ':' + pw
            it = it + '@'
        it = it + host

        if port != '':
            it = it + ':' + port

    if destdir != '':
        if destdir[0] != '/':
            it = it + '/'
        it = it + destdir

#  print "urlJoin it=", it
    return it


def addStandardOptions(parser):
    """ Add standard options to a optparse list of options.

    just so this code does not have to be repeated.
    """
    parser.add_option( "--dataDir", dest="dataDir", default=FET_DATA,
        help="root of directory tree where data is stored", metavar="PXDATA")
    parser.add_option( "-e", "--etcdir", dest="etcDir",
        default=FET_ETC, help="Directory for configuration files",
        metavar="PXETC")
    parser.add_option( "-s", "--source", default=None, dest="source",
        help="name of source (when receiving) identifying config and queue directories" )
    parser.add_option( "-c", "--client", default=None, dest="client",
        help="name of client (when tranmitting) identifying config and queue directories" )
    parser.add_option( "-d", "--suppress_debug", default=100, type="int",
        dest="debug", help="makes it ridiculously more voluble"  )



def lockStopOrDie(lfn, cmd):
    """ cmd=start: lock & continue or die,  cmd=stop: kill running pid.

       If the command is 'stop' then stop the process in question.
       the lockfile path gives the location of the process (pid in file.)
       which may be running.  Attempt to kill the process.  Whether or not
       it succeeds, unlink the lock file (so that 'stop' followed by 'start'
       tends to bring one to a reasonable state.)

       if the command is start, and there is no lock file indicating that
       another process is currently using the directory, then create a lock
       file containing the pid of the calling process.
    """
    createDir( os.path.dirname(lfn) )
    if os.path.exists( lfn ):
        lockfile = open( lfn , 'r' )
        lockpid = int(lockfile.read())
        lockfile.close()
        if cmd == 'stop':
            try:
                os.kill(lockpid,signal.SIGTERM)
            except:
                pass
            try:
                os.unlink( lfn )
            except:
                pass

            sys.exit(0)
        elif cmd == 'reload' :
            try:
                os.kill(lockpid,signal.SIGHUP)
                sys.exit(0)
            except:
                pass
            sys.exit(1)
        else:
            print "FATAL: queue locked by process: " + repr(lockpid)
            sys.exit(1)

    else:
        if cmd == 'stop':
            print "ERROR: no lock file (" + lfn + ") found doing nothing. "
            sys.exit(0)

    lockfile = open( lfn , 'w' )
    lockfile.write( repr(os.getpid()) )
    lockfile.close()



#
# config reader
#



"""
  fills global 'patterns' list of the form:

  clients is a keyed data structure...
      filled with list values of the form:
  [ [ patterns, default_dest, connect_timeout, type, ordering, batch, ... ] ... ]

"""
clients = {}

#
# FIXME: This isn't done right, there should be a parent class
#        with inheritance to override it.  but this is just a skeleton.
#
# -- for a file sender
clientdefaults = [ [], '',10,'single-file','MultiKeysStringSorter',200,'3','000'  ]
#

# FIXME: currently get one global list of clients.
#        if it were structured such that all the patterns were per client
#        indices, then it could break out faster on first match.
#

def readClients(logger):
    """ read the client configuration directory

    this provides all the information necessary for routing files to
    their tx queues and the information needed for file transmission.
    """
    global clients
    global clientdefaults

    clients = {}

    for cfname in os.listdir( FET_ETC + 'tx/' ):
        if cfname[-5:] != '.conf':
            continue
        cliconf = open( FET_ETC + 'tx/' + cfname, 'r' )
        clientid = cfname[:-5]
        mask=cliconf.readline()
        destdir=''
        client=clientdefaults
        patterns = []
        protocol = 'ftp'
        user=''
        password=''
        host=''
        port=''
        destdir=''
        destfn=''
        while mask :
            maskline = mask.split()
            if ( len(maskline) >= 2 and not re.compile('^[ \t]*#').search(mask) ) :
                if maskline[0] == 'imask' :
                    destination=urlJoin(protocol,destdir,user,password,host,port)
                    #print "destination: ", destination
                    patterns = patterns + [ maskline + [ destination, destfn ] ]
                elif maskline[0] == 'emask':
                    patterns = patterns + [ maskline ]
                elif maskline[0] == 'directory':
                    destdir = maskline[1]
                elif maskline[0] == 'destination':
                    ( protocol, dirspec, uspec, pwspec, hspec, pspec ) = \
                          urlSplit( maskline[1] )
                    if len(maskline) > 2 :
                        destfn = maskline[2]
                    if dirspec != '':
                        destdir = dirspec
                    if uspec != '':
                        user = uspec
                    if pwspec != '':
                        password = pwspec
                    if hspec != '':
                        host = hspec
                    if pspec != '':
                        port = pspec
                    if client[1] == '':
                        client[1]=urlJoin(protocol,destdir,user,password,host,port)

                    #print "after urlSplit proto="+ protocol +" destdir="+ destdir +' u='+ user +' pw='+ password +' h='+ host  +' port='+ port
                elif maskline[0] == 'host':
                    host = maskline[1]
                elif maskline[0] == 'user':
                    user = maskline[1]
                elif maskline[0] == 'filename':
                    destfn = maskline[1]
                elif maskline[0] == 'password':
                    password = maskline[1]
                elif maskline[0] == 'type':
                    client[3] = maskline[1]
                elif maskline[0] == 'protocol':
                    protocol = maskline[1]
                elif maskline[0] == 'connect_timeout':
                    client[2] = int(maskline[1])
                elif maskline[0] == 'order':
                    client[4] = maskline[1]
                elif maskline[0] == 'batch':
                    client[5] = int(maskline[1])
            mask=cliconf.readline()

        cliconf.close()
        client[0] = patterns
        clients[clientid] = copy.deepcopy(client)
        logger.writeLog( logger.DEBUG, "read config of client " + clientid )
        client[1]=''
        host=''
        port=''
        user=''
        password=''
        destdir=''
        destfn=''

    # dump clients db
    #for k in clients.keys():
    #   print "client ", k, " is: ",  clients[k], "\n"

    #print "\n\n\nPatterns\n\n\n"
    #print patterns



sources = {}
"""

  source is an associative array of source attributes.

  each source is a list of the form:

  [ priority, extension, type ]

priority...
      number, default priority.

extension... mapping to ingestname:
      [ what ] : ori_system : ori_site : data_type : data_format/priority :

      [what] is the unadorned file name, the thing that is being extended.

sample
      sacn444_bidule : input_source : origin_site : BULLETIN/PHOTO/CHART/RADAR
      datafmt ASCII/JPEG/........ :


type -- URL indicating connection type
        am://localhost:4012

"""
sourcedefaults = {
    'extension':':MISSING:MISSING:MISSING:MISSING:MISSING',
    'type':None,
    'mapEnteteDelai':None,
    'port':0,
    'AddSMHeader':False,
 }

def readSources(logger):
    """ read the source configuration directory for settings
    """
    global sources
    global sourcedefaults

    sources = {}

    #print "readSources"
    for cfname in os.listdir( FET_ETC + 'rx/' ):
        if cfname[-5:] != '.conf':
            continue

        sourceid = cfname[:-5]
        srcconf = open( FET_ETC + 'rx/' + cfname, 'r' )
        source = sourcedefaults.copy()
        src=srcconf.readline()
        while src :
            srcline=src.split()
            if ( len(srcline) >= 2 and not re.compile('^[ \t]*#').search(src) ) :
                try:
                 
                    if srcline[0] == 'extension':
                       if len(string.join(srcline[1:]).split(':')) != 5:
                          logger.writeLog( logger.ERROR, "wrong number of fields in extension " + sourceid + " config: " + src )
                       else:
                           source[srcline[0]] = ':' + string.join(srcline[1:])
                    elif srcline[0] == 'arrival':
                        source['mapEnteteDelai'] =  { srcline[1] : ( int(srcline[2]), int(srcline[3]) )  }
                    elif srcline[0] == 'AddSMHeader' and isTrue(srcline[1]):
                        source[srcline[0]] = True
                    else:
                        source[srcline[0]] = string.join(srcline[1:])
                except:
                    logger.writeLog( logger.ERROR, "error in " + sourceid + " config: " + src )

            src=srcconf.readline()

        srcconf.close()

        sources[sourceid] = copy.deepcopy(source)
        logger.writeLog( logger.DEBUG, "read config of source " + sourceid )


def readCollections(options,logger):
    """read collection parameters from default configuration file.
       reads info from /apps/px/etc/collection.conf
       see comments in that file for parameter details.
    """
    options.delaiMaxSeq = 23
    options.extension = None
    options.collectionParams={}

    collcfg = open( FET_ETC + 'collection.conf', 'r' )
    cfline = collcfg.readline()
    while cfline:
        cf = cfline.split()
        if (len(cf) > 0 ) and not re.compile('^[ \t]*#').search(cfline) :
            if cf[0] == 'collect':
                try:
                    exec( "options.collectionParams['"+ cf[1] +"']=" + string.join(cf[2:]) )
                except:
                    logger.writeLog(logger.ERROR, "error in collect spec: " + cfline )
            elif cf[0] == 'tooLate':
                options.DelaiMaxSeq = int(cf[1])
            elif cf[0] == 'extension':
                options.extension = cf[1]
        cfline = collcfg.readline()
    collcfg.close()

def sourceQDirName(s):
    return FET_DATA + FET_RX + s

def ingestName(r,s):
    """ map reception to ingest name, based on the source configuration.

        This just inserts missing fields,  like whattopds.  DUMB!
        FIXME: have a library of functions, configurable per source, to
           perform the mapping, perhaps using rmasks ? & other args.
    """
    rs = r.split(':')
    print rs
    ss = sources[s]['extension'].split(':')
    print ss

    if ( len(rs) == 1 ) or rs[1] == '' :
        rs = rs + [ ss[1] ]
    if len(rs) == 2 or rs[2] == '' :
        rs = rs + [ ss[2] ]
    if len(rs) == 3 or rs[3] == '' :
        rs = rs + [ ss[3] ]
    if len(rs) == 4 or rs[4] == '' :
        rs = rs + [ ss[4] ]
    if len(rs) == 5 or rs[5] == '' :
        rs = rs + [ ss[5] ]
    rs = rs + [ time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) ) ]

    print "Final string: %s" % string.join(rs, ':')
    return string.join(rs,':')


def dbName(ingestname):
    """ given an ingest name, return an relative database name

    given a file name of the form:
        what : ori_system : ori_site : data_type : format :
    link it to
        db/<today>/type/ori_system/ori_site/ingestname
    (same pattern as PDS)
    path is relative to FET_DATA (includes db)

    NB: see notes/tests.txt for why the date/time is recalculated everytime.
    """
    if ingestname.count(':') >= 4 :
        dirs = ingestname.split(':')
        today = time.strftime( "%Y%m%d/", time.gmtime(time.time()) )
        return FET_DATA + 'db/' + today + dirs[3] + '/' + dirs[1] + '/' + dirs[2] + '/' + ingestname
    else:
        return ''

def clientQDirName(client, ingestname):
    """Return the directory into which a file of a given priority should be placed.
    A couple of different layouts being contemplated.
    /apps/px/txq/<client>/YYYYmmddhh ??
    """
    global clients
    parts = ingestname.split(":")
    priority = parts[4].split(".")[0]
    return FET_DATA + FET_TX + client + '/'+ priority + '/' +  time.strftime( "%Y%m%d%H", time.gmtime(time.time()) ) + '/'

def clientMatch(c,ingestname):

    for p in clients[c][0]:
        if fnmatch.fnmatch(ingestname,p[1]) :
            if p[0] == 'imask':
                return p
            else:
                return []
    return []


def clientMatches(ingestname):
    """ returns a list of clients to whome the file with ingestname should be sent.

     match ingestname against global list of client patterns.

     return a list of clients which should
          [ [ client, host, dir ], [ client, host, dir ], ... ]
    """

    global clients

    hits=[]

#  print "client matches for " + ingestname
    for c in clients.keys():
        p = clientMatch(c,ingestname)
        if p != []:
            hits = hits + [ [ c ] + p ]

#  print hits
    return hits

def destFileName(ingestname, climatch):
    """ return the appropriate destination give the climatch client specification.

    return the appropriate destination file name for a given client match from patterns.

    DESTFN=fname -- change the destination file name to fname
    WHATFN       -- change the file name
    HEADFN       -- Use first 2 fieds of as the destination file name
    NONE         -- use the entire ingest name, except...
    TIME or TIME:   -- TIME stamp appended
    TIME:RASTER:COMPRESS:GZIP -- modifiers... hmm... (forget for now...)
    SENDER        -- SENDER=

    FIXME: unknowns:
      SENDER not implemented
      is DESTFN:TIME allowed? reversing order
      does one add <thismachine> after TIME ?
      INFO Jul 22 17:00:01: /apps/pds//bin//pdsftpxfer: INFO: File SACN59_CWAO_221600_RRB_208967:AMTCP2FILE-EXT:PDS1-DEV:BULLETIN:ASCII::20040722164923:pds1-dev   sent to ppp1.cmc.ec.gc.ca as    SACN59_CWAO_221600_RRB_208967    Bytes= 75
      pdschkprod-bulletin-francais.20050109:INFO Jan 09 16:09:15: pdschkprod 1887: Written 3867 bytes: /apps/pds/pdsdb/BULLETIN/tornade/CMQ/ACC-FP55WG7409160137:tornade:CMQ:BULLETIN:ASCII:SENDER=ACC-FP55WG7409160137X.TXT:20050109160915
      pdschkprod-bulletin-francais.20050109:INFO Jan 09 16:13:39: pdschkprod 1887: Written 4972 bytes: /apps/pds/pdsdb/BULLETIN/tornade/CMQ/ACC-FP54XK7309160151:tornade:CMQ:BULLETIN:ASCII:SENDER=ACC-FP54XK7309160151X.TXT:20050109161339
      p
      What do the RASTER etc... options do? just add suffix?

    """

# print "climatch: ", climatch
    specs=climatch[3].split(':')
#  print 'climatch[4] is +' + climatch[4] + '+'
    dname=ingestname.split(':')[0]
    time_suffix=''

    for spec in specs:
        if spec == 'TIME':
            time_suffix= ':' + time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) )
        elif (spec == 'WHATFN') or (spec == ''):  # blank results from "TIME" alone as spec
            dfn=dname
	elif spec == 'HEADFN':
	    head=dname.split('_')
	    dfn=head[0] + '_' + head[1]
        elif spec == 'NONE':
            dfn=ingestname
        elif re.compile('DESTFN=.*').match(spec):
            dfn=spec[7:]
        elif (spec[0:4] == 'RASTER') or (spec[0:4] == 'COMPR' ):
            dfn= dname + ':' + spec
        elif spec[0] == '/':
            dfn= spec[4] + '/' + dname # local directory name
        elif spec == 'SENDER':
            dfn= (dname[5].split('='))[1]
        else:
            print 'ERROR: do not understand destfn parameter: ', climatch
            return ''

    return dfn + time_suffix

"""avoid onerous repeated calls to os.path.exists, by short-circuiting after
   first check.

   FIXME: cleaning out dirs_created? might get big after a while.
      cleaned out in initDB.
"""
dirs_created = []

def createDir(dir):
    """ create a directory if it does not exist

    should I check for rollover?
    """
    global dirs_created

    if not (dir in dirs_created):
        dirs_created  = dirs_created + [ dir ]
        if not os.path.exists(dir):
            try:
                os.makedirs( dir, 01775 )
            except OSError, e:
                #FIXME: Should I log this?
                print e

def linkFile(f,l):
    """ make a link l to the existing file f,
    """
    createDir( os.path.dirname(l) )
#  print "link(", f, l, ")"
    #print "link %s %s" % (f, l)
    os.link( f, l )
    # Introduced this sleep to verify that there is not
    # other problems
    #time.sleep(2)


def directIngest(ingestname,clist,lfn,logger):
    """ link lfn into the db & client spools based on ingestname & clients
        accepts a list of matching clients.
    """

    dbn=dbName(ingestname)
    if ( dbn == '' ):
        return 0

    linkFile(lfn, dbn)
    logger.writeLog( logger.INFO, "ingest " + dbn )

    if len (clist) < 1:
        return 1

    # Problem bulletins are databased, but not sent to clients
    if not (ingestname.find("PROBLEM_BULLETIN") == -1):
       return 1
    
    for c in clist:
        cname=clientQDirName(c, ingestname)
        linkFile(dbn , cname + ingestname)

    logger.writeLog( logger.INFO, "queued for " + string.join(clist) )
    return 1

def ingest(ingestname,lfn,logger):
    """ link lfn into the database & client spools, based on ingestname & pri

       apply all the masks to ingestname to find the clients who should receive
       it, and insert it in their queues.
    """

    clist=map( lambda x: x[0], clientMatches(ingestname))
    return directIngest(ingestname,clist,lfn,logger)


def initDB(logger):
    """
    initialize the base of the FET spooling tree, rotating the today link
    if needed.

    FIXME: Are there race conditions because of db rollover. ?
         -- added explicit creation based on current time to dbName,
            so that it doesn't depend on system wide db rollover process.

    so nothing below matters, because nobody uses 'today'.  it is only sugar for humans.

    N.B. There are potential race conditions if multiple ingestors run.
    really, ingest process should be quiescent when the symlink changes.
         -- both look at the directories and try to roll over at once.
         -- both try to move the symbolic link at a rollover time.
         -- Others try to reference 'today' while it doesn't exist.
            most built-in processes should use the real directory.
         -- really, only writers to db should be the ingestors.

    Checking a lock every time would be horridly expensive for a once
    a day event. so they only place this should be called is from somewhere
    that knows the db is quiescent.

    a lock for only the initDB routing would solve most (except 'today' reference)

    FIXME: -- creation of yesterday link doesn't happen if today is missing.
           -- no logging of this important event, hmm...
    """
    global dirs_created
    global FET_DB

    logger.writeLog( logger.INFO, "dbinit start")
    dirs_created = []
    createDir( FET_DATA + '/.' )
    createDir( FET_DATA + FET_RX )
    createDir( FET_DATA + FET_TX )
    createDir( FET_DATA + FET_CL )
    createDir( FET_DATA + FET_TMP )
    createDir( FET_DATA + "db" )
    todaylink = time.strftime( "%Y%m%d", time.gmtime(time.time()))
    FET_DB = "db/" + todaylink + "/"
    createDir( FET_DATA + FET_DB )
    tl = FET_DATA + "db/today"
    yl = FET_DATA + "db/yesterday"
    if os.path.exists( tl ):
        lnk = os.readlink( tl )
        if ( todaylink != lnk ):
            try:
                os.unlink( tl )
                os.symlink( todaylink, tl )
            except OSError:
                # FIXME: Bad way (try, except) to handle a concurrency problem
                (type, value, tb) = sys.exc_info()
                logger.writeLog(logger.ERROR, "Type: %s, Value: %s" % (type, value))
                pass                   

            if os.path.exists( lnk ):
                try:
                    os.unlink( yl )
                    os.symlink( lnk, yl )
                except OSError:
                    # FIXME: Bad way (try, except) to handle a concurrency problem
                    (type, value, tb) = sys.exc_info()
                    logger.writeLog(logger.ERROR, "Type: %s, Value: %s" % (type, value))
                    pass                   

    else:
        try:
            os.symlink( todaylink, tl )
        except OSError:
            # FIXME: Bad way (try, except) to handle a concurrency problem
            (type, value, tb) = sys.exc_info()
            logger.writeLog(logger.ERROR, "Type: %s, Value: %s" % (type, value))
            pass                   

        if os.path.exists( yl ):
            try:
                os.unlink( yl )
            except OSError:
                # FIXME: Bad way (try, except) to handle a concurrency problem
                (type, value, tb) = sys.exc_info()
                logger.writeLog(logger.ERROR, "Type: %s, Value: %s" % (type, value))
                pass                   

    logger.writeLog( logger.INFO, "dbinit done")


def startup(opts, logger):
    global FET_DATA
    global FET_ETC
    global options

    options = opts
    FET_DATA=opts.dataDir
    if FET_DATA[-1] != '/':
        FET_DATA = FET_DATA + '/'

    FET_ETC=opts.etcDir
    if FET_ETC[-1] != '/':
        FET_ETC = FET_ETC + '/'

    options.use_pds=False
    try:
        pxconf = open( FET_ETC + 'px.conf', 'r' )
        cf=pxconf.readline()
        while cf:
            cfl=cf.split()
            if cfl[0] == 'usePDS':
                options.use_pds=isTrue(cfl[1])
            cf=pxconf.readline()
        pxconf.close()
    except:
        logger.writeLog( logger.INFO, "could not open global px config: " +
                FET_ETC + 'px.conf'  )

    if not options.use_pds:
        initDB(logger)

    readClients(logger)
    readSources(logger)
    if os.path.exists(FET_ETC + "collection.conf"):
        readCollections(options,logger)
    if options.client:
        if options.client in clients.keys():
            opts.type = clients[options.client][3]
            dd = urlSplit(clients[options.client][1])
            opts.host = dd[4]
            opts.port = dd[5]
            opts.connect_timeout = int(clients[options.client][2])
            opts.sorter = 'MultiKeysStringSorter'
            opts.numFiles = 100
            opts.batch = clients[options.client][5]
        else:
            logger.writeLog( logger.ERROR, "unknown client: " + options.client )

    elif options.source:
        if options.source in sources.keys():
            s=sources[options.source]
            opts.port = int(s['port'])
            opts.extension = s['extension']
            opts.mapEnteteDelai = s['mapEnteteDelai']
            opts.AddSMHeader = s['AddSMHeader']
        else:
            logger.writeLog( logger.ERROR, "unknown source: " + options.source )
    elif options.type == 'collector':
        pass

# module initialization code
#startup()
