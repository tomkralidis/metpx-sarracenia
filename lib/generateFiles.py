import sys, string, random

#root = "/apps/pds/tools/ColumboNCCS/testfiles1/"
root = "/home/ib/dads/dan/progProj/pds-nccs/bulletins/tata/"
#root = "/apps/px/tx/senderWMO/"
numFiles = sys.argv[1]
size = sys.argv[2]
letters = list(string.letters)
priority = range(1,6)
timestamp = 2005020174200

for num in range(int(numFiles)):
    timestamp = timestamp + 1
    output = open(root + "SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:" + str(random.choice(priority)) + ".A.I.E.C.M.N.H.K.X.S.D.O.Q.::" + str(timestamp), 'w')
    randomString = "".join(map(lambda x: random.choice(letters), range(0, int(size))))
    output.write(randomString)
    output.close()

root = "/home/ib/dads/dan/progProj/pds-nccs/bulletins/titi/"
for num in range(int(numFiles)):
    timestamp = timestamp + 1
    output = open(root + "SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:" + str(random.choice(priority)) + ".A.I.E.C.M.N.H.K.X.S.D.O.Q.::" + str(timestamp), 'w')
    randomString = "".join(map(lambda x: random.choice(letters), range(0, int(size))))
    output.write(randomString)
    output.close()

root = "/home/ib/dads/dan/progProj/pds-nccs/bulletins/toto/"
for num in range(int(numFiles)):
    timestamp = timestamp + 1
    output = open(root + "SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:" + str(random.choice(priority)) + ".A.I.E.C.M.N.H.K.X.S.D.O.Q.::" + str(timestamp), 'w')
    randomString = "".join(map(lambda x: random.choice(letters), range(0, int(size))))
    output.write(randomString)
    output.close()