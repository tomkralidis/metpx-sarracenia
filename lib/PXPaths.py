"""
#############################################################################################
# Name: PXPaths.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-16
#
# Description: Useful PX Paths
#
#############################################################################################
"""
def normalPaths():

    global ROOT, BIN, LIB, LOG, ETC, RXQ, TXQ, DB, RX_CONF, TX_CONF

    ROOT = '/apps/px/'
    BIN = ROOT + 'bin/'
    LIB = ROOT + 'lib/'
    LOG = ROOT + 'log/'
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'rxq/'
    TXQ = ROOT + 'txq/'
    DB = ROOT + 'db/'
    RX_CONF = ETC + 'rx/'
    TX_CONF = ETC + 'tx/'

def drdbPaths():

    global ROOT, BIN, LIB, LOG, ETC, RXQ, TXQ, DB, RX_CONF, TX_CONF

    ROOT = '/apps2/px/'
    BIN = ROOT + 'bin/'
    LIB = ROOT + 'lib/'
    LOG = '/apps/px/' + 'log/'
    ETC = ROOT + 'etc/'
    RXQ = ROOT + 'rxq/'
    TXQ = ROOT + 'txq/'
    DB = ROOT + 'db/'
    RX_CONF = ETC + 'rx/'
    TX_CONF = ETC + 'tx/'
