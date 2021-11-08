# PJSIP-PSUA2

This project helps to understand and build VOIP endpoints with PJSIP-PSUA2 api.

Provide opportunties to work with multiple languages.

Documentation:

From multiple sources:
 - stackoverflow, 
 - githubs, 
 - medium articles

specifically on both pjsua (older/decprecated) and psua2

https://docs.pjsip.org/en/2.10/api/pjsua2.html  <br />
https://docs.pjsip.org/en/latest/pjsua2/intro_pjsua2.html <br />

relevant information regarding PSJIP-PSUA:

pjsua - https://www.pjsip.org/release/0.5.4/PJSIP-Dev-Guide.pdf <br />
pjsua2 - https://www.pjsip.org/docs/book-latest/PJSUA2Doc.pdf

### 3.2.4 Threading

For platforms that require polling, the PJSUA2 module provides its own worker thread to poll PJSIP, so it is not
necessary to instantiate own your polling thread. Having said that the application should be prepared to have the
callbacks called by different thread than the main thread. The PJSUA2 module itself is thread safe. <br />

Often though, especially if you use PJSUA2 with high level languages such as Python, it is required to disable PJSUA2
internal worker threads by setting:
 - EpConfig.uaConfig.threadCnt to 0

### Docker info & build

- working image based on python:3.9.6-slim-buster and VERSION_PJSIP=2.10 
- https://github.com/pjsip/pjproject/archive/2.10.tar.gz
- Need to resolve build issue(s) with 2.11 onward 

### Current implementation:

- InboundVOIPCall.py can handle multiple inbound calls. Call max count is at 4. it will cycle (0,1,2,3). 
- OutboundVOIPCall.py dials out on specific call to Callee. 
