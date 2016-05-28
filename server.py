#!/usr/bin/python
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import os
import json
import uuid
from datetime import datetime
from threading import Timer


resources = {}
clients = {}

def checkTimeOut():
    for resource in resources :
        if resources[resource]['current_user']:
            if (datetime.now()-resources[resource]['current_user']["last_request"]).total_seconds()>1.5 :  # big value not real time
                sentMsg = {"type" : "error" , "resource" : resource, "status" : "timeout"}
                clients[resources[resource]["current_user"]['id']].write_message(sentMsg)
                pushWaitingUser(resource)
            for index, waiting_client in enumerate(resources[resource]['accessQueue']):
                if (datetime.now() - waiting_client['demanded_at']).total_seconds() > 3 :    # big value not real time
                    sentMsg = {"type" : "error" , "resource" : resource, "status" : "timeout"}
                    clients[resources[resource]["accessQueue"][index]].write_message(sentMsg)
                    del resources[resource]["accessQueue"][index]

            sentMsg = {"type" : "check_resource" , "resource" : resource, "release_key" : resources[resource]['release_key']}
            clients[resources[resource]["current_user"]['id']].write_message(sentMsg)


def pushWaitingUser(resource):
    if len(resources[resource]["accessQueue"])>0:
        newClientId = resources[resource]["accessQueue"][0]['id']
        resources[resource]["current_user"]={"id" : newClientId, "last_request" : datetime.now()}
        del resources[resource]["accessQueue"][0]
        sentMsg = {"type" : "use_resource" , "resource" : resource, "release_key" : resources[resource]['release_key']}
        clients[newClientId].write_message(sentMsg)
    else:
        resources[resource]["current_user"] = {}


def detectDeadlock (client_id, demandedResource):  # detect simple deadlock not chain deadlock
    for resource in resources :
        if resources[resource]["current_user"]['id'] == client_id:
            for index, waiting_client in enumerate(resources[resource]['accessQueue']):
                if waiting_client['id'] == resources[demandedResource]["current_user"]['id'] :   # if deadlock send messages to both services causing deadlock
                    print "deadlock at "+ demandedResource + " and "+resource
                    sentMsg = {"type" : "error" , "resource" : demandedResource, "status" : "deadlock"}
                    clients[client_id].write_message(sentMsg)
                    sentMsg = {"type" : "error" , "resource" : resource, "status" : "deadlock"}
                    clients[resources[demandedResource]["current_user"]['id']].write_message(sentMsg)
                    #del resources[resource]["accessQueue"][index]
    pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("client.html")

class CentralLockingHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        self.client_id = str(uuid.uuid4())
        clients[self.client_id]= self
        sentMsg = {"type" : "connection_details" , "client_id" : self.client_id}
        self.write_message(sentMsg)

    def on_message(self, message):
        message = dict(json.loads(message))
        msgType = message['type']
        print msgType
        
        if msgType == "demand_resource":

            if message['resource'] not in resources.keys() :
                release_key = str(uuid.uuid4())+str(uuid.uuid4())
                print release_key
                resources[message['resource']] = {"current_user" : {"id" : self.client_id , "last_request" : datetime.now()} , "accessQueue" : [] , "release_key" : release_key}
                sentMsg = {"type" : "use_resource" , "resource" : message['resource'], "release_key" : release_key}
                self.write_message(sentMsg)

            elif not resources[message['resource']]["current_user"] :
                resources[message['resource']]["current_user"] = {"id" : self.client_id, "last_request" : datetime.now()}
                sentMsg = {"type" : "use_resource" , "resource" : message['resource'], "release_key" : resources[message['resource']]['release_key']}
                self.write_message(sentMsg)

            elif not ( any(waiting_client['id'] == self.client_id for waiting_client in resources[message['resource']]["accessQueue"]) or resources[message['resource']]["current_user"]['id'] == self.client_id )  :
                resources[message['resource']]["accessQueue"].append({"id" : self.client_id, "demanded_at" : datetime.now()})
                detectDeadlock(self.client_id, message['resource'])

        elif msgType == "release_resource":
            print "release message body "+str(message)
            print "resource to be released" + str (resources[message['resource']])
            if message['resource'] in resources.keys()  and message['release_key'] == resources[message['resource']]['release_key'] and self.client_id == resources[message['resource']]['current_user']['id'] :
                print "release me man"
                pushWaitingUser (message['resource'])

        elif msgType == "check_resource_response":  # is needed at all ?! yes
            if message['resource'] in resources.keys()  and message['release_key'] == resources[message['resource']]['release_key'] and self.client_id == resources[message['resource']]['current_user']['id'] :
                resources[message['resource']]["current_user"]["last_request"] = ""

        elif msgType == "use_resource_response":
            if message['resource'] in resources.keys()  and message['release_key'] == resources[message['resource']]['release_key'] and self.client_id == resources[message['resource']]['current_user']['id'] :
                print message["status"]
                if message['status'] == "ok" :
                    
                    resources[message['resource']]["current_user"]["last_request"] = ""
                else :
                    pushWaitingUser(message['resource'])
            
        print str(resources)
    def close(self, code=None, reason=None):
        del clients[self.client_id]
        pass # check if client is in que or currently using any resources


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

app = tornado.web.Application([(r'/',MainHandler),(r'/central_locking',CentralLockingHandler)])
server = tornado.httpserver.HTTPServer(app)
server.listen(9191)
tornado.ioloop.IOLoop.current().start()
#rt = RepeatedTimer(5, checkTimeOut)
