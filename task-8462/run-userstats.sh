#!/bin/sh
set -e
echo `date` "Starting."
echo `date` "Downloading descriptors."
rsync -arz --delete --exclude 'relay-descriptors/votes' metrics.torproject.org::metrics-recent in
echo `date` "Parsing descriptors."
javac -d bin/ -cp lib/commons-codec-1.6.jar:lib/commons-compress-1.4.1.jar:lib/descriptor.jar src/Parse.java
java -cp bin/:lib/commons-codec-1.6.jar:lib/commons-compress-1.4.1.jar:lib/descriptor.jar Parse
for i in $(ls out/*.sql)
do
  echo `date` "Importing $i."
  psql -f $i userstats
done
echo `date` "Exporting results."
psql -c 'COPY (SELECT * FROM estimated) TO STDOUT WITH CSV HEADER;' userstats > userstats.csv
echo `date` "Terminating."

