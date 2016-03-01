#!/bin/bash

LOC=`readlink -f $0`
LOC=`dirname $LOC`
SEDFILE=$LOC/global.sed
echo $SEDFILE

if [ "$1" == "-f" ]
then
   SEDFILE=$2
   shift
   shift
fi
   
for x in $@
do
    echo $x
    mv $x $x.old
    sed -f -r $SEDFILE $x.old  > $x
done;
read -r -p "Delete *.old files ?" ans 
case "$ans" in
[yY][eE][sS]) rm -f *.old;;
[yY])         rm -f *.old;;
esac

