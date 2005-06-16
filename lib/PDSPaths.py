"""
#############################################################################################
# Name: PDSPaths.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-16
#
# Description:
#
#############################################################################################
"""

def normalPaths():

    # Useful directories
    global ROOT, BIN, LOG, ETC, RXQ, TXQ, DB, INFO, RX_CONF, TX_CONF
    global PROD, SWITCH, STARTUP, TOGGLE, RESEND
    global FULLPROD, FULLSWITCH, FULLSTARTUP, FULLTOGGLE

    ROOT = '/apps/pds/'
    BIN = ROOT + 'bin/'
    LOG = ROOT + 'log/'
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'RAW/'
    TXQ = ROOT + 'home/'
    DB = ROOT + 'pdsdb/'
    INFO = ROOT + 'info/'
    RX_CONF = ETC
    TX_CONF = ETC 

    # Useful files
    PROD = "pdschkprod.conf"
    SWITCH = "pdsswitch.conf"
    STARTUP = "PDSstartupinfo"
    TOGGLE = "ToggleSender"
    RESEND = "pdsresend"

    # Useful paths (directory + file)
    FULLPROD = ETC + PROD
    FULLSWITCH = ETC + SWITCH
    FULLSTARTUP = INFO + STARTUP
    FULLTOGGLE = BIN + TOGGLE

def drdbPaths():
    """
    The only difference with normalPaths is the ROOT (apps2)
    """
    global ROOT, BIN, LOG, ETC, RXQ, TXQ, DB, INFO, RX_CONF, TX_CONF
    global PROD, SWITCH, STARTUP, TOGGLE, RESEND
    global FULLPROD, FULLSWITCH, FULLSTARTUP, FULLTOGGLE

    # Useful directories
    ROOT = '/apps2/pds/'
    BIN = ROOT + 'bin/'
    LOG = '/apps/pds/' + 'log/'  # We always want to log on /apps
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'RAW/'
    TXQ = ROOT + 'home/'
    DB = ROOT + 'pdsdb/'
    INFO = ROOT + 'info/'
    RX_CONF = ETC
    TX_CONF = ETC 

    # Useful files
    PROD = "pdschkprod.conf"
    SWITCH = "pdsswitch.conf"
    STARTUP = "PDSstartupinfo"
    TOGGLE = "ToggleSender"
    RESEND = "pdsresend"

    # Useful paths (directory + file)
    FULLPROD = ETC + PROD
    FULLSWITCH = ETC + SWITCH
    FULLSTARTUP = INFO + STARTUP
    FULLTOGGLE = BIN + TOGGLE

