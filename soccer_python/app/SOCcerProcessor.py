import json
import math
import os
import smtplib
import time
import logging
import urllib
import subprocess

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twisted.internet import reactor, defer
from PropertyUtil import PropertyUtil
from stompest.async import Stomp
from stompest.async.listener import SubscriptionListener
from stompest.async.listener import DisconnectListener
from stompest.config import StompConfig
from stompest.protocol import StompSpec
import urllib

class soccerProcessor(DisconnectListener):
  CONFIG = 'queue.config'
  NAME = 'queue.name'
  URL = 'queue.url'

  def composeMail(self,recipients,message,files=[]):
    config = PropertyUtil(r"config.ini")
    print "sending message"
    if not isinstance(recipients,list):
      recipients = [recipients]
    packet = MIMEMultipart()
    packet['Subject'] = "Your request has been processed"
    packet['From'] = "SOCcer<do.not.reply@nih.gov>"
    packet['To'] = ", ".join(recipients)
    print recipients
    print message
    packet.attach(MIMEText(message,'html'))
    for file in files:
      with open(file,"rb") as openfile:
        packet.attach(MIMEApplication(
          openfile.read(),
          Content_Disposition='attachment; filename="%s"' % os.path.basename(file),
          Name=os.path.basename(file)
        ))
    MAIL_HOST=config.getAsString('mail.host')
    print MAIL_HOST
    smtp = smtplib.SMTP(MAIL_HOST)
    smtp.sendmail("do.not.reply@nih.gov",recipients,packet.as_string())

  def testQueue(self):
    print("tested")

  def rLength(self, tested):
    if tested is None:
      return 0
    if isinstance(tested,list) or isinstance(tested,set):
      return len(tested)
    else:
      return 1

 # @This is the consume code which will listen to Queue server.
  def consume(self, client, frame):
    print "In consume"
    files=[]
    parameters = json.loads(frame.body)
    print parameters
    inputFileId=str(parameters['inputFileId'])
    fileName=str(parameters['fileName'])
    timestamp=str(parameters['timestamp'])
    url=str(parameters['url'])
    url=urllib.unquote(url).decode('utf8')
    socSystem = str(parameters["socSystem"])
    if(socSystem=="model10"):
      model="1.0"
    else:
      model="1.1"
    print(inputFileId)

    if socSystem=="model10":
      return_code = subprocess.call(['/usr/local/jdk1.7/bin/java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
    else:
      return_code = subprocess.call(['java', '-cp', 'Java_API_1_1.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
    print("calclulated")
    filePath = os.path.join('/local/content/analysistools/public_html/results/soccer/files', inputFileId)
    with open(filePath + '_response.json', 'r') as resultFile:
        responseObj = resultFile.read().replace('\n', '')
    print('response object: ' + responseObj)
    os.remove(filePath + '_response.json')
    print(url)
    Link='<a href='+url+'></a>'
    print(Link)
    print parameters['timestamp']
    print "Here is the Link to the past:"
    print Link
    body = """
            <p>The file ("""+fileName+""") you uploaded using model """+model+""" on """+timestamp+""" has been processed. </p>
            <p>You can view the result page at: """+url+""".  This link will expire two weeks from today.</p>
            </br>
            <p> - SOCcer Team</p>
            <p>(Note:  Please do not reply to this email. If you need assistance, please contact NCISOCcerWebAdmin@mail.nih.gov)</p>
          </div>
          """

    message = """
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>html title</title>
      </head>
      <body>"""+body+"""</body>"""

          #    "\r\n\r\n - JPSurv Team\r\n(Note:  Please do not reply to this email. If you need assistance, please contact xxxx@mail.nih.gov)"+
          #    "\n\n")
    print "sending"
    self.composeMail(parameters['emailAddress'],message,files)
    print "end"

  @defer.inlineCallbacks
  def run(self):
    client = yield Stomp(self.config).connect()
    headers = {
        # client-individual mode is necessary for concurrent processing
        # (requires ActiveMQ >= 5.2)
        StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
        # the maximal number of messages the broker will let you work on at the same time
        'activemq.prefetchSize': '100',
    }
    client.subscribe(self.QUEUE, headers, listener=SubscriptionListener(self.consume, errorDestination=self.ERROR_QUEUE))
    client.add(listener=self)

  # Consumer for Jobs in Queue, needs to be rewrite by the individual projects

  def onCleanup(self, connect):
    print 'In clean up ...'

  def onConnectionLost(self, connect, reason):
    print "in onConnectionLost"
    self.run()

 # @read from property file to set up parameters for the queue.
  def __init__(self):
    config = PropertyUtil(r"config.ini")
     # Initialize Connections to ActiveMQ
    self.QUEUE=config.getAsString(soccerProcessor.NAME)
    self.ERROR_QUEUE=config.getAsString('queue.error.name')
    config = StompConfig(config.getAsString(soccerProcessor.URL))
    self.config = config

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  soccerProcessor().run()
  reactor.run()
