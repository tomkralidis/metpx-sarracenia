"""
#############################################################################################
# Name: CacheManager.py
#
# Author: Daniel Lemay
#
# Date: 2005-06-30
#
# Description: U
#
#############################################################################################

"""
import md5
import os, os.path, sys, commands, re, pickle, time, logging, fnmatch

class CacheManager(object):

    MINUTE = 60                     # Number of seconds in a minute
    HOUR = 60 * MINUTE              # Number of seconds in an hour 

    def __init__(self, maxEntries, timeout = 3 * HOUR):
        self.cache = {}
        self.maxEntries = maxEntries
        self.timeout = timeout

    def add(self, key):
        #print "Was new"
        if len(self.cache) < self.maxEntries:
            self.cache[key] = [time.time(), 1]
        else:
            #print "Was full, try TimeoutClear"
            self.TimeoutClear()
            if len(self.cache) < self.maxEntries:
                #print "TimeoutClear was sufficient"
                self.cache[key] = [time.time(), 1]
            else:
                # Remove the least recently used (LRU) item
                #print "TimeoutClear was insufficient, we delete LRU"
                temp = [(item[1][0], item[0]) for item in self.cache.items()]
                temp.sort()            
                del self.cache[temp[0][1]]
                # Add the new key
                self.cache[key] = [time.time(), 1]

    def find(self, object):
        key = md5.new(object).hexdigest()
        if key in self.cache:
            self.cache[key][0] = time.time()
            self.cache[key][1] += 1
            #print "Was cached"
            return self.cache[key]
        else:
            self.add(key)
            return None

    def clear(self):
        self.cache = {}

    def TimeoutClear(self):
        # Remove all the elements that are older than oldest acceptable time
        print self.getStats()
        oldestAcceptableTime = time.time() - self.timeout
        for item  in self.cache.items():
            if item[1][0] < oldestAcceptableTime:
                del self.cache[item[0]]

    def getStats(self):

        compteurs = {}

        for item in self.cache.items():
            if item[1][1] in compteurs:
                compteurs[item[1][1]] += 1
            else:
                compteurs[item[1][1]] = 1
        
        total = 0.0
        cached = 0.0

        for (key, value) in compteurs.items():
            cached += (key-1) * value
            total += key * value

        #percentage = "%2.2f %% of the last %i requests were cached (implied %i files were deleted)" % (cached/total * 100,  total, cached)

        return (compteurs, cached, total)

if __name__ == '__main__':
  
    manager = CacheManager(maxEntries=3, timeout=5 * 3600)

    manager.find('toto')
    manager.find('tutu')
    time.sleep(6)
    #print manager.cache

    manager.find('titi')
    manager.find('toto')
    #print manager.cache
    manager.find('mimi')
    #print manager.cache
    print manager.getStats()
