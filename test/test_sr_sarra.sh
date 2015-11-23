#!/bin/ksh


# This test suppose rabbitmq server installed
# with default configuration  guest,guest administrator

# getting rabbitmqadmin

rm rabbitmqadmin* 2> /dev/null
wget http://localhost:15672/cli/rabbitmqadmin
chmod 755 rabbitmqadmin

# configuring tester user as sarra requieres

./rabbitmqadmin -u guest -p guest declare user \
     name=tester password=testerpw tags=

./rabbitmqadmin -u guest -p guest declare permission \
     vhost=/  user=tester \
     configure='^q_tester.*$' write='xs_tester' read='^q_tester.*$|^xl_tester$'

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xs_tester type=topic auto_delete=false durable=true

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xs_guest type=topic auto_delete=false durable=true

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xpublic type=topic auto_delete=false durable=true

echo $#

if [[ $# != 2 ]]; then
   echo $0 user password
   exit 1
fi

echo killall sr_sarra.py

killall sr_sarra.py > /dev/null 2>&1
rm ./sr_sarra_*.log ./.sr_sarra_* ./toto* ./test/t* ./sarra_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

export USER=$1
export PASSWORD=$2

cat << EOF > toto
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456
89abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF
cat << EOF > toto.p0
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456
EOF
cat << EOF > toto.p1
89abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF

# published files

cp toto    /var/www/test/toto
cp toto    /apps/px/test/toto

cp toto.p0 toto.128.2.0.0.d.Part
cp toto.p0 /var/www/test/toto.128.2.0.0.d.Part
cp toto.p0 /apps/px/test/toto.128.2.0.0.d.Part

cp toto.p1 toto.128.2.0.1.d.Part
cp toto.p1 /var/www/test/toto.128.2.0.1.d.Part
cp toto.p1 /apps/px/test/toto.128.2.0.1.d.Part

chmod 777 toto* /var/www/test/toto* /apps/px/test/toto*

cat << EOF > sarra_test1.conf

# source

source_broker amqp://guest@localhost/
source_exchange xs_guest
source_topic v02.post.#

sftp_user $USER
sftp_password $PASSWORD

ftp_user $USER
ftp_password $PASSWORD

queue_name q_guest.sr_sarra.test

source_from_exchange True
from_cluster alta

# destination

broker amqp://guest@localhost/
exchange xpublic
document_root /

EOF

mkdir -p ~/.config/sarra 2> /dev/null
echo 'from_cluster alta' > ~/.config/sarra/sarra.conf

mkdir ./test

echo ==== INPLACE FALSE ====

function test1 {

      ../sarra/sr_sarra.py $* start   > /dev/null 2>&1
      #======== 1
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02 -to cluster1,cluster2,alta  > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_02|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02 -to cluster1,cluster2,alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02 -to cluster1,cluster2,alta
         exit 1
      fi
      rm   ./test/toto_02*

      #======== 1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03 -to alta > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_03|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03 -to alta
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03 -to alta
         exit 1
      fi
      rm   ./test/toto_03*

      #======== 1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_04 -to alta > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_04|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04 -to alta
         exit 1
      fi
      rm   ./test/toto_04*

      #======== 1

      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_05 -to alta > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_05|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05 -to alta
         exit 1
      fi
      rm   ./test/toto_05*

      #parts I

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128 -to alta > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_06.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_06.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_06*

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128 -to alta > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_07.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_07*

      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_08.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_08.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_08*

      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_09.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_09.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_09*


      #parts P

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_10 -p p -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_10 -p p -to alta > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_10.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_10.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p -to alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p -to alta
         exit 1
      fi
      rm   ./test/toto_10*

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_11 -p p -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_11 -p p -to alta > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_11.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_11.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p -to alta
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p -to alta
         exit 1
      fi
      rm   ./test/toto_11*

      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_12 -p p -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_12 -p p -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_12.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_12.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p -to alta
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p -to alta
         exit 1
      fi
      rm   ./test/toto_12*

      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_13 -p p -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_13 -p p -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_13.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_13.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p -to alta
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p -to alta
         exit 1
      fi
      rm   ./test/toto_13*

      
      ../sarra/sr_sarra.py $* stop > /dev/null 2>&1


}

#test1 --url file:                ./sarra_test1.conf

mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_FALSE

echo ==== INPLACE TRUE ====

function test2 {

      ../sarra/sr_sarra.py $* start > /dev/null 2>&1

      #======== 1
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14 -to alta > /dev/null 2>&1
      sleep 2
      ls -al toto ./test/*
      N=`diff toto ./test/toto_14|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14 -to alta
         exit 1
      fi
      rm   ./test/toto_14*

      #======== 1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15 -to alta > /dev/null 2>&1
      sleep 3
      ls -al toto ./test/*
      N=`diff toto ./test/toto_15|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15 -to alta
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15 -to alta
         exit 1
      fi
      rm   ./test/toto_15*

      #======== 1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_16 -to alta > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_16|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16 -to alta
         exit 1
      fi
      rm   ./test/toto_16*
      sleep 2

      #======== 1
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_17 -to alta > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_17|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17 -to alta
         exit 1
      fi
      rm   ./test/toto_17*
      sleep 2

      #parts I

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128 -to alta > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_18|wc -l`
      if ((N==0)) ; then
         echo OK  ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_18*

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128 -to alta > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_19|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_19*

      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_20|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_20*


      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_21|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128 -to alta
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128 -to alta
         exit 1
      fi
      rm   ./test/toto_21*


      #parts P

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_22 -p p -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_22 -p p -to alta > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_22|wc -l`
      if ((N==0)) ; then
         echo OK  ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p  -to alta
      else
         echo ERROR ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p -to alta
         exit 1
      fi
      rm   ./test/toto_22*

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_23 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_23 -p p  -to alta > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_23|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p -to alta 
      else
         echo ERROR ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p -to alta 
         exit 1
      fi
      rm   ./test/toto_23*

      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_24 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_24 -p p  -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_24|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p -to alta 
      else
         echo ERROR ../sarra/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p -to alta 
         exit 1
      fi
      rm   ./test/toto_24*

      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_25 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_25 -p p  -to alta > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_25|wc -l`
      if ((N==0)) ; then
         echo OK ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p -to alta 
      else
         echo ERROR ../sarra/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p -to alta 
         exit 1
      fi
      rm   ./test/toto_25*

      ../sarra/sr_sarra.py $* stop > /dev/null 2>&1

}

#test2 --mirror True --url file: --inplace True ./sarra_test1.conf
mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_TRUE

echo ==== INPLACE FALSE NOT MODIFIED ====

function test3 {

      cp ./toto ./test/toto2
      cp ./toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part
      cp ./toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part

      ../sarra/sr_sarra.py $* start > /dev/null 2>&1
      #======== 1
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2   -to alta > /dev/null 2>&1

      #======== 1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2  -to alta > /dev/null 2>&1

      #======== 1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2  -to alta > /dev/null 2>&1

      #======== 1
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2  -to alta > /dev/null 2>&1

      #parts I

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128  -to alta > /dev/null 2>&1


      #parts P

      #======== 2
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1

      #======== 2
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      #======== 2
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      #======== 2
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1
      ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p  -to alta > /dev/null 2>&1

      
      sleep 10
      ls -al toto ./test/*

      ../sarra/sr_sarra.py $* stop > /dev/null 2>&1

      N=`grep modified sr_sarra_sarra_test1_0001.log  | wc -l`
      if ((N==20)) ; then
         echo OK  not modified in all cases
      else
         echo ERROR should have 20 cases of unmodified files
         exit 1
      fi
      rm   ./test/toto2*
 
      ../sarra/sr_sarra.py $* stop > /dev/null 2>&1

}

#test3 --mirror True --url file:                ./sarra_test1.conf
mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_FALSE_NOT_MODIFIED

echo ==== INSTANCES AND INSERTS ====

function test4 {

         ../sarra/sr_sarra.py $* ./sarra_test1.conf start > /dev/null 2>&1

         ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_26 -p i,1 -r   -to alta > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/*
               N=`diff toto ./test/toto_26|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSTANCES/INSERTS
               else
                  echo ERROR file:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_26*

         ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_27 -p i,1 -r  -to alta > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/*
               N=`diff toto ./test/toto_27|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSTANCES/INSERTS
               else
                  echo ERROR http:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_27*

         ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_28 -p i,1 -r  -to alta > /dev/null 2>&1
         
               sleep 40
               ls -al toto ./test/*
               N=`diff toto ./test/toto_28|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSTANCES/INSERTS
               else
                  echo ERROR sftp:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_28*

         ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_29 -p i,1 -r  -to alta > /dev/null 2>&1
         
               sleep 40
               ls -al toto ./test/*
               N=`diff toto ./test/toto_29|wc -l`
               if ((N==0)) ; then
                  echo OK ftp:   INSTANCES/INSERTS
               else
                  echo ERROR ftp:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_29*

         ../sarra/sr_sarra.py $* ./sarra_test1.conf stop  > /dev/null 2>&1
         sleep 10

}

test4 --mirror True --url file: --inplace true --instances 100 

cat sr_sarra_sarra_test1_*.log >> sr_sarra_sarra_test1_0001.log_INSTANCES_INSERT
rm sr_sarra_sarra_test1_*.log


echo ==== INSTANCES AND INSERTS AND TRUNCATE ====

function test5 {

         ../sarra/sr_sarra.py $* ./sarra_test1.conf start > /dev/null 2>&1

         cat toto | sed 's/12345/abcde/' > ./test/toto_30
         echo abc >> ./test/toto_30

         ../sarra/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_30 -p i,11 -r  -to alta  > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/*
               N=`diff toto ./test/toto_30|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSERTS and TRUNCATED
               else
                  echo ERROR file:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_30*


         cat toto | sed 's/12345/abcde/' > ./test/toto_31
         echo abc >> ./test/toto_31

         ../sarra/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_31 -p i,11 -r  -to alta > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/*
               N=`diff toto ./test/toto_31|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSERTS and TRUNCATED
               else
                  echo ERROR http:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_31*


         cat toto | sed 's/12345/abcde/' > ./test/toto_32
         echo abc >> ./test/toto_32

         ../sarra/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_32 -p i,11 -r  -to alta > /dev/null 2>&1
         
               sleep 60
               ls -al toto ./test/*
               N=`diff toto ./test/toto_32|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSERTS and TRUNCATED
               else
                  echo ERROR sftp:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_32*

         cat toto | sed 's/12345/abcde/' > ./test/toto_33
         echo abc >> ./test/toto_33

         ../sarra/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_33 -p i,11 -r  -to alta > /dev/null 2>&1
         
               sleep 60
               ls -al toto ./test/*
               N=`diff toto ./test/toto_33|wc -l`
               if ((N==0)) ; then
                  echo OK ftp:   INSERTS and TRUNCATED
               else
                  echo ERROR ftp:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_33*

         sleep 10
         ../sarra/sr_sarra.py $* ./sarra_test1.conf stop > /dev/null 2>&1

}

test5 --mirror True --url file: --inplace true --instances 10
cat sr_sarra_sarra_test1_*.log >> sr_sarra_sarra_test1_0001.log_INSTANCES_INSERT_TRUNCATE
rm sr_sarra_sarra_test1_*.log

rm ./sr_sarra_*.log ./.sr_sarra_* ./toto* ./test/t* ./sarra_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1
