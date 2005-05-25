#!/usr/bin/env python2
import sys, string, random, shutil

#original = "SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:3.A.I.E::20050201200339"
original = "WACN34_CWUL_220101_32182:ncp1:CWUL:WA:1:Direct:20050322010209"
#root = "/apps/px/txq/dummyAMIS/"
#root = "/apps/px/rxq/yap/"
root = "/apps/px/txq/wmoDan/1/"
numFiles = sys.argv[1]
priority = range(1,2)
timestamp = 20050201174200

for num in range(int(numFiles)):
    timestamp = timestamp + 1
    shutil.copy("/apps/px/bulletins/1/" + original, root + "SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:" + 
                 str(random.choice(priority)) + ".A.I.E::" + str(timestamp))

