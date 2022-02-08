import json
import logging
import types
import socketio

from aiortc import RTCIceCandidate, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
from events import Events # Note you must pip install events

logger = logging.getLogger(__name__)
BYE = object()
connectedUserSocketId = ""

def object_from_string(message_str):
    message = json.loads(message_str)
    if message["type"] in ["answer", "offer"]:
        return RTCSessionDescription(**message)
    elif message["type"] == "candidate" and message["candidate"]:
        candidate = candidate_from_sdp(message["candidate"].split(":", 1)[1])
        candidate.sdpMid = message["id"]
        candidate.sdpMLineIndex = message["label"]
        return candidate
    elif message["type"] == "bye":
        return BYE


def object_to_string(obj):
    if isinstance(obj, RTCSessionDescription):
        message = {"sdp": obj.sdp, "type": obj.type}
    elif isinstance(obj, RTCIceCandidate):
        message = {
            "candidate": "candidate:" + candidate_to_sdp(obj),
            "id": obj.sdpMid,
            "label": obj.sdpMLineIndex,
            "type": "candidate",
        }
    else:
        assert obj is BYE
        message = {"type": "bye"}
    return json.dumps(message, sort_keys=True)

#        self.__events = Events('on_pre_offer', 'on_answer') #, 'on_ice_candidate')

class Event(object):
 
    def __init__(self):
        self.__eventhandlers = []
 
    def __iadd__(self, handler):
        self.__eventhandlers.append(handler)
        return self
 
    def __isub__(self, handler):
        self.__eventhandlers.remove(handler)
        return self
 
    def __call__(self, *args, **keywargs):
        for eventhandler in self.__eventhandlers:
            eventhandler(*args, **keywargs)


class SocketIOSignaler():
    def __init__(self, host, port):
        self.onPreOffer = Event()
        self.onAnswer = Event()
        self.onIceCandidate = Event()
        self._host = host
        self._port = port
        self.sio = socketio.Client()

        #self.onPreOffer = self.__events.on_pre_offer
        #self.onAnswer = self.__events.on_answer
        #self.onIceCandidate = self.__events.on_ice_candidate
        
        @self.sio.event
        def message(data):
            print('I received a message!')

        @self.sio.on('broadcast')
        def on_broadcast( data ):
            if data['eventname'] == 'ACTIVE_USERS':
                activeUsers = data['activeUsers']
                print (activeUsers)
                #for peerUser in activeUsers:
                 #   print(peerUser['username'])
                  #  print(peerUser['socketId'])
                   # if peerUser['socketId'] != self.sio.sid:
                    #    peer = peerUser
                     #   break
            print('I received a broadcast message!')

        @self.sio.on('webRTC-candidate')
        def on_ice_candidate( data ):
            print(data)
            self.onIceCandidate(data)
            print('I received a on_ice_candidate message!')

        @self.sio.on('pre-offer')
        def on_pre_offer( data ):
            print(data)
            global connectedUserSocketId
            connectedUserSocketId = data['callerSocketId']
            self.onPreOffer(data)
            print('I received a pre-offer message!')

        @self.sio.on('webRTC-answer')
        def on_answer( data ):
            print(data)
            self.onAnswer(data)
            print('I received a answer message!')

        @self.sio.event
        def message(data):
            print(data)

        @self.sio.on('connection')
        def on_connection(data):
            #mySocketId = data
            self.sio.emit("register-new-user", {'username':'python-test-user', 'socketId':data})
            print('I received a connection!', data)

        @self.sio.event
        def connect():
            print("I'm connected!")

        @self.sio.event
        def connect_error(data):
            print("The connection failed!")

        @self.sio.event
        def disconnect():
            print("I'm disconnected!")

        self.sio.connect('http://10.0.0.160:5000')

    def ConnectToServer():
        url = "http://10.0.0.160:5000"

    async def ConnectToServer(self):
        url = "http://{}:{}".format(self._host, self._port)
        await self.sio.connect(url)

    async def close(self):
        self.sio.disconnect()
#            await self.send(BYE)

    async def sendWebRtcOffer(self, descr):
        #sdpJson = object_to_string(descr)
        self.sio.emit("webRTC-offer", {'calleeSocketId':connectedUserSocketId, 'offer':descr.sdp})

    def message(data):
        print('I received a message!')

    def on_message(data):
        print('I received a message!')

    def connect():
        print("I'm connected!")

    def connect_error(data):
        print("The connection failed!")

    def disconnect():
        print("I'm disconnected!")

    def on_broadcast(data):
        print('I received a broadcast onevent!')

    def broadcast(data):
        print('I received a broadcast event!')


def add_signaling_arguments(parser):
    """
    Add signaling method arguments to an argparse.ArgumentParser.
    """
    parser.add_argument(
        "--signaling",
        "-s",
        choices=["copy-and-paste", "tcp-socket", "unix-socket"],
    )
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Signaling host (tcp-socket only)"
    )
    parser.add_argument(
        "--signaling-port", default=1234, help="Signaling port (tcp-socket only)"
    )
    parser.add_argument(
        "--signaling-path",
        default="aiortc.socket",
        help="Signaling socket path (unix-socket only)",
    )


def create_signaler(args):
    """
    Create a signaling method based on command-line arguments.
    """
    #if args.signaling == "tcp-socket":
    #return SocketIOSignaler(args.signaling_host, args.signaling_port)
    return SocketIOSignaler("10.0.0.160", "5000")
