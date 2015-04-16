#!/bin/bash

if [ -e "$1" ]
then
java -cp "lib/*" -Dgov.nih.cit.soccer.wordnet.dir="/local/content/soccer/dict" -Dgov.nih.cit.soccer.output.dir="/local/content/tomee/webapps/soccer/files" gov.nih.cit.soccer.Soccer $1
Rscript /local/content/tomee/webapps/soccer/WEB-INF/classes/SoccerResultPlot.R $2 $3
else
echo "$1 does not exist!"
fi
