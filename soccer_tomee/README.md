## SOCcer Build and Deployment

> Created by Sue Pan, last modified on Jul 02, 2015

SOCcer is composed of two applications: webapp and client. Therefore, there are two build.xml files. Read the following instructions thoroughly before deploying both applications.
#### 1. Pull the source codes from github

Git link: https://github.com/CBIIT/nci-webtools-dceg-classification.git 
```
$ rm -rf nci-webtools-dceg-classification.old
$ mv nci-webtools-dceg-classification nci-webtools-dceg-classification.old
$ git clone https://github.com/CBIIT/nci-webtools-dceg-classification.git
```
#### 2. Deploy web application 

Working directory: nci-webtools-dceg-classification/soccer/webapp
##### a. Issue ant deploy command

Define the following variables when executing ant deploy command:
```
1. soccer.domain.name=soccer-dev.nci.nih.gov                  // Modify soccer domain name accordingly (dev, stage, prod)
2. tomee.dir=/local/content/tomee                             // The installation folder of TomEE plus
3. soccer.dir=/local/content/soccer                           // Soccer related folder     
4. gov.nih.cit.soccer.wordnet.dir=/local/content/soccer/dict  // The folder of WordNet dictionary
5. gov.nih.cit.soccer.rscript=/usr/bin/Rscript                // Whereis Rscript command
```
For example,
```
$ ant -Dsoccer.domain.name=soccer-dev.nci.nih.gov -Dtomee.dir=/local/content/tomee -Dsoccer.dir=/local/content/soccer -Dgov.nih.cit.soccer.wordnet.dir=/local/content/soccer/dict -Dgov.nih.cit.soccer.rscript=/usr/bin/Rscript deploy
```
**Note:** Please make sure the directories reference in the build properties are already created and exist on the server.  Ant deploy compiles the source codes, generates soccer.war and tomee.xml files, then copies the soccer.war to <tomee.dir>/webapps folder, and copies the tomee.xml to <tomee.dir>/conf folder, so please make sure the user has write permission to both <tomee.dir>/webapps and <tomee.dir>/conf directories.  
##### b. Restart TomEE Plus
```
$ service tomee restart
```
#### 3. Deploy client application

Working directory: nci-webtools-dceg-classification/soccer/client
##### a. Issue ant deploy command

Define the following variables when executing ant deploy command:
```
1. soccer.domain.name=soccer-dev.nci.nih.gov                  // Modify soccer domain name accordingly (dev, stage, prod)
2. tomee.dir=/local/content/tomee                             // The installation folder of TomEE plus   
3. soccer.dir=/local/content/soccer                           // Soccer related folder   
4. soccer.remote.web.port=80                                  // The port# to access SOCcer web application through the soccer.domain.name defined above
5. gov.nih.cit.soccer.wordnet.dir=/local/content/soccer/dict  // The folder of WordNet dictionary
6. gov.nih.cit.soccer.rscript=/usr/bin/Rscript                // Whereis Rscript command   
7. deploy.target.dir=/local/content/soccer                    // Where to deploy the client application
```
For example,

    $ ant -Dsoccer.domain.name=soccer-dev.nci.nih.gov -Dtomee.dir=/local/content/tome -Dsoccer.dir=/local/content/soccer -Dsoccer.remote.web.port=80 -Dgov.nih.cit.soccer.wordnet.dir=/local/content/soccer/dict -Dgov.nih.cit.soccer.rscript=/usr/bin/Rscript -Ddeploy.target.dir=/local/content/soccer deploy

**Note:** Please make sure the directories reference in the build properties are already created and exist on the server.  Ant deploy compiles the source codes, copies all the artifacts in the dist folder to the target folder designated by -Ddeploy.target.dir above, and if the OS is Linux/Unix, adds execute (+x) permission to the jcmd.sh script.
##### b. Start client application
```
$ service soccer stop
$ service soccer start
$ tail -f /local/content/soccer/soccer.log  
```
If you are able to see the following message: "INFO: Request to run </local/content/soccer/jcmd.sh> every <10> seconds.", congratulations, the client application is running well.
#### 4. Open soccer web link in web browser and test the application.
