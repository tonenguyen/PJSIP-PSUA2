
import pjsua2 as pj
import time 
import wave
import credentials as cr

# This example of pjsua2 python dials an outbound call. 
# Incorporated from multiple stackoverflow questions and Mr Tyler Long
# Code based on pjsip-apps of pjsua 2call.py and ringcentral example 
# https://www.pjsip.org/docs/book-latest/PJSUA2Doc.pdf
# https://github.com/pjsip/pjproject/blob/master/pjsip-apps/src/pygui/call.py
# https://github.com/ringcentral/ringcentral-pjsip/blob/master/demos/call-and-play-wav-file.cpp

# pg 37


class Account(pj.Account):

   # SIP Registration 
   def onRegState(self, prm):
       ai = pj.Account.getInfo(self)
       print("#####", ai)
       print ("***OnRegState: " + prm.reason)

class Call(pj.Call):
  
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.connected = False
        self.playbackMedia = ""
        
    def setplaybackMedia(self, playbackFile="" ):
      self.playbackMedia=playbackFile
    
    def getplaybackMediaDuration(self):
        #https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration
        
        # determine the playback duration
        if (self.playbackMedia):
          wfile = wave.open(self.playbackMedia, "rb")
          # duration = total number of frames / playback frame rate
          return  (1.0 * wfile.getnframes ()) / wfile.getframerate ()
    
    def handleMedia(self, ci):
        if not (ci):
            ci = self.getInf()

        # check for media type and status since we can have
        # more than one media types (audio, video)

        for  mi in  ci.media:
          # we just want audio 
          if mi.type == pj.PJMEDIA_TYPE_AUDIO and \
              mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
              
              # get the proper audioMedia player currently joined the bridge
              m = self.getMedia(mi.index)
              am = pj.AudioMedia.typecastFromMedia(m)

              # create playback and stream back the proper audioMedia player
              player = pj.AudioMediaPlayer()
              player.createPlayer(self.playbackMedia)

              # send the audio stream 
              player.startTransmit(am)

              # Allow the proper wait time  while transmit the audio stream
              # Otherwise, transmission will terminate right away

              playbackMediaDuration = self.getplaybackMediaDuration()

              for _ in range(0, int(playbackMediaDuration)):
                  if (pj.Call.isActive()):
                      time.sleep(1)
              
              # clean up the call after finish the call
              pj.Call.hangup()
              break

    def onCallState(self, prm):

      #callInfo
      ci = self.getInfo()

      if (ci.state == pj.PJSIP_INV_STATE_CONFIRMED):
        # call is connected
        self.connected = True
        # refactor to `handle media cleaner
        self.handleMedia(ci)
       # if call is no longer connected, disconnect
       elif (ci.state == pj.PJSIP_INV_STATE_DISCONNECTED):
          exit(0)

# pjsua2 test function

def pjsua2_test():
    # Everything starts with an endpoint. pg 21 
    # create &  initialize the library of a single endpoint.

    #default configuration & customization
    ep_cfg = pj.EpConfig() 
    # extra logging for troubleshooting
    ep_cfg.logConfig.level=4

    #Python does not like PJSUA2's thread due to GIL. It will result in segment fault.
    #This also possibly introduces issues with being stuck in pool

    ep_cfg.uaConfig.threadCnt = 0; 
    ep_cfg.uaConfig.userAgent = cr.userAgentTag

    #endpoint instantiate 
    ep = pj.Endpoint()
    #create library 
    ep.libCreate()
    # initialize lib
    ep.libInit(ep_cfg)
    
    # Create SIP transport. Error handling sample is shown pg 22

    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 5060
    

    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)
    # if using TCP, registrarURI needs to append at end ";transport=tcp"
    ep.transportCreate(pj.PJSIP_TRANSPORT_TCP, sipTpConfig)

    # Start the library/ep
    ep.libStart()

    # https://www.pjsip.org/pjsip/docs/html/classpj_1_1AudDevManager.htm#a7ae55533e9570e741f70f9240b6699cb
    # Need to initialize audioDev to NULL as there are no real audio devices
    ep.audDevManager().setNullDev()

    #Account provide identity of user (URI) pg 39
    #Account configuration idURI/registrarUri/Authenication  
    acfg = pj.AccountConfig()
    acfg.idUri = "sip:" + cr.userID + "@" + cr.sipDomain
    acfg.regConfig.registrarUri = "sip:" + cr.sipDomain + ";" + cr.sipTPMode
    acfg.userAgent = cr.userAgentTag
    #acfg.sipConfig.proxies = "sip:" + cr.outboundProxy
    
    cred = pj.AuthCredInfo("digest", "*", cr.userID, 0, cr.password)
    acfg.sipConfig.authCreds.push_back(cred)
    #acfg.sipConfig.getProxi
    
    # Create the account with the proper registration info
    # send the SIP REGISTER to the server 
    acc = Account()
    acc.create(acfg)
    time.sleep(2)

    # initialize Call class with the proper SIP acc
    myCall = Call(acc)
    myCall.setplaybackMedia(playbackFile=cr.playbackMedia)
    
    #default call parameter/can further customize
    prm = pj.CallOpParam()
    #dial an outbound call
    myCall.makeCall("sip:"+cr.calleeNumber+"@"+cr.sipDomain, prm)
    
    # Polling for the events otherwise will terminate after a few events
    # https://stackoverflow.com/questions/62289196/pjsip-client-does-not-ack-invite-response
    while True:
      ep.libHandleEvents(10)
      

    # Destroy the library / end of ep
    ep.libDestroy()

#
# main()
#
if __name__ == "__main__":
  pjsua2_test()

