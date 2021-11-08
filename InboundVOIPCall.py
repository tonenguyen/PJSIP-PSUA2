# This pjsua2 python will handle inbound calls until press Ctrl+C 
# Bug(s) need to be flushed out for handling Caller hangup
# https://www.pjsip.org/docs/book-latest/html/reference.html#
# Toan Nguyen 

import pjsua2 as pj
import time
import wave
import credentials as cr
import signal

#https://docs.python.org/3/library/signal.html
def handler(signum, frame):
    print("Exiting via ctrl-C")
    # missing the proper handling here
    exit(0)
    
# signal handler from python's main thread to handle (Ctrl+C)
# define the handler function before calling signal.signal
signal.signal(signal.SIGINT, handler)  

#class Account handles all SIP registration along with incomingCall
class Account(pj.Account):
        
    def __init__(self, ep=None):
        pj.Account.__init__(self)
        # Link the account to the endpoint
        self.ep = ep 
        # important flag to track call object status
        # critical when call object is no longer avail (deleted)
        self.isCurrentCallActive = False 
        # track an active call object
        self.currentCall = None

    # SIP Registration
    def onRegState(self, prm):
        ai = pj.Account.getInfo(self)
        print("#####", ai)
        print("***OnRegState: " + prm.reason)

    def onIncomingCall(self, iprm):
        
        # Check if any active calls before create an Call instance 
        # dont answer twice as it will terminate the incoming call unless
        # merging call later on
        if not self.isCurrentCallActive:   
            #instance of Call with iprm.callId to handle incoming call
            self.currentCall = Call(self, iprm.callId)
            self.isCurrentCallActive = True

#class Call handles different states of the call - answer, playback, teardown the call

class Call(pj.Call):

    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        print("INITIALIZE CallerID", call_id)
        # must have an registered account associated with calls 
        self.acc = acc
        # start & end time of a given call 
        self.startTime = 0
        self.endTime = 0 
        self.playbackMedia = "AUDIO_FILE"

    def setplaybackMedia(self, playbackFile=""):
        self.playbackMedia = playbackFile

    def getplaybackMediaDuration(self):
        # https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration
        # determine the playback duration
        if (self.playbackMedia):
            wfile = wave.open(self.playbackMedia, "rb")
            # duration = total number of frames / playback frame rate
            duration = wfile.getnframes() / wfile.getframerate()
            wfile.close()
            return duration

    def onCallTsxState(self, prm):
        ci = self.getInfo()
        print("onCallTsxState -----", ci.stateText)

    def onCallState(self, prm):

        ci = self.getInfo()
        # https://www.pjsip.org/pjsip/docs/html/group__PJSIP__INV.htm
        print("I keep changing state - on Call State here", ci.stateText)
        # once account onIncoming instantiates Call and call state = INCOMING
        # answer the call. Need to look into merging call
        if (ci.state == pj.PJSIP_INV_STATE_INCOMING):
            prm0 = pj.CallOpParam()
            prm0.statusCode = pj.PJSIP_SC_OK
            self.answer(prm0)

        if (ci.state == pj.PJSIP_INV_STATE_CONFIRMED):
            
            print("I will send audio when we established CONFIRMED STATE")
            self.handleMedia(ci)
        
        # if call is no longer connected, disconnect and delete currentCall
        elif (ci.state == pj.PJSIP_INV_STATE_DISCONNECTED):
            print("Clean up in CALL DISCONNECT")

            # clean up call by deleting the current Call instance 
            # & reset currentCallActive flag
            if self.acc.isCurrentCallActive == True:
                try:             
                    del self.acc.currentCall
                    self.acc.isCurrentCallActive = False 
                except NameError:
                    print("acc.currentCall does not exist!")


    def handleMedia(self, ci):
        # check for media type and status since we can have
        # more than one media types (audio, video)
        for mi in ci.media:
            # we just want audio
            print("CHECK audio info", self.getMedia(mi.index))
            if mi.type == pj.PJMEDIA_TYPE_AUDIO and \
                    mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:

                # get the proper audioMedia player currently joined the bridge
                m = self.getMedia(mi.index)
                am = pj.AudioMedia.typecastFromMedia(m)

                # create playback and stream back the proper audioMedia player
                player = pj.AudioMediaPlayer()
                print('currrent state of the call before playback', ci.stateText)
                
                # set manual portion
                playbackMediaDuration = cr.setCallDuration
                self.setplaybackMedia(playbackFile=cr.playbackMedia)
                
                # Need additional error handling here
                print(self.playbackMedia)
                player.createPlayer(self.playbackMedia)

                # send the audio stream
                player.startTransmit(am)

                # Allow the proper time  while transmit the audio stream - blocking
                # Otherwise, transmission will terminate right away

                for i in range(0, int(playbackMediaDuration)):
                    # interrupt handler implementation here.
                    # acc.ep.libHandleEvents(100)
                    #only wait when call is still active
                    if not pj.Call.isActive(self):
                        break
                        #print('waiting inside', ci.stateText)
                    time.sleep(1)   
                print("I am done here - tear down")
                player.stopTransmit(am)
                # clean up the call after finish the call
                self.hangup(pj.CallOpParam())
                

# pjsua2 test function
def pjsua2_test():

    # create &  initialize the library of a singleton endpoint.

    # default configuration & customization
    ep_cfg = pj.EpConfig()
    # extra logging for troubleshooting
    ep_cfg.logConfig.level = 1
    # Python does not like PJSUA2's thread. It will result in segment fault
    ep_cfg.uaConfig.threadCnt = 0
    ep_cfg.uaConfig.userAgent = cr.userAgentTag
    
    # endpoint instantiate
    ep = pj.Endpoint()
    # create library
    ep.libCreate()
    # initialize lib
    ep.libInit(ep_cfg)

    # Create SIP transport. Error handling sample is shown pg 22

    sipTpConfig = pj.TransportConfig()
    sipTpConfig.port = 5060

    # if using TCP, registrarURI needs to append at end ";transport=tcp"
    ep.transportCreate(pj.PJSIP_TRANSPORT_TCP, sipTpConfig)

    # Start the library/ep
    ep.libStart()

    # https://www.pjsip.org/pjsip/docs/html/classpj_1_1AudDevManager.htm#a7ae55533e9570e741f70f9240b6699cb
    # Initialize audioDev to NULL since no real audio devices 
    ep.audDevManager().setNullDev()

    # Account configuration idURI/registrarUri/Authenication
    acfg = pj.AccountConfig()
    acfg.idUri = "sip:" + cr.userID + "@" + cr.sipDomain
    acfg.regConfig.registrarUri = "sip:" + cr.sipDomain + ":5060;" + cr.sipTPMode
    acfg.userAgent = cr.userAgentTag
    # Sip authenication of userID & password
    cred = pj.AuthCredInfo("digest", "*", cr.userID, 0, cr.password)
    acfg.sipConfig.authCreds.push_back(cred)

    #https://www.pjsip.org/docs/book-latest/html/reference.html#structpj_1_1AccountConfig
    # Disable lockCodecEnabled
    # Ok with first invite (SDP),  don't want an re-invite with one codec adjustment
    acfg.mediaConfig.lockCodecEnabled=False

    # Create the account with the proper registration info
    # send the SIP REGISTER to the server

    acc = Account(ep)
    acc.create(acfg)
    time.sleep(1)

    #block outbound for now to test
    """# initialize Call class with the proper SIP acc
    myCall = Call(acc)

    # set up media playback file. Need error check here or defaulting value
    myCall.setplaybackMedia(playbackFile=cr.playbackMedia)

    # default call parameter/can further customize
    prm = pj.CallOpParam()
    # dial an outbound call
    myCall.makeCall("sip:"+cr.calleeNumber+"@"+cr.sipDomain, prm)"""
    
 
    # Polling for the events otherwise will terminate after a few events
    while True:
        ep.libHandleEvents(100)
        time.sleep(1)
        currentCallTime = time.perf_counter() 
        # hang up the call after current call exceeds the set call duration
        # implementation here
       #print(f"In the event handler currentTime {currentCallTime} endTime {endTime}")     

    # Destroy the library / end of ep
    ep.libDestroy()

#
# main()
#
if __name__ == "__main__":
    pjsua2_test()
