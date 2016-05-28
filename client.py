import websocket
import json
import thread
import time
import sys
import threading


myId = ""

resources = {}

def on_message(ws, message):
	global myId
	print(message)
	message = dict(json.loads(message))
	if "type" in message :

		msgType = message['type']
		if msgType == "use_resource":

			if message['resource'] in resources :
                                resources[message['resource']]["lock"].releasse()
				resources[message['resource']]["release_key"] = message['release_key']
				status = "ok"
			else :
				status = "Fail"
			
			sentMsg = {"type" : "use_resource_response" , "resource" : message['resource'], "release_key" : message['release_key'],"client_id" : myId,"status" : status}
			write_message(sentMsg)

		elif msgType == "check_resource":
			sentMsg={"resource":message['resource'],"client_id" : myId,"type":"check_resource_response","release_key" : resources[message['resource']]['release_key']}
			write_message(sentMsg)

		elif msgType == "connection_details":
			myId = message['client_id']

		elif msgType == "error":
			if message['status'] == "timeout":
				if resource in resources :
					del resources[resource] 
				print "timeout on "+ message['resource']

			elif message['status'] == "deadlock":
				print "deadlock on "+message['resource']

def write_message(msg):
	try:
		ws.send(json.dumps(msg))
	except Exception, e:
		ws.close()
	

def on_error(ws, error):
	#print(error)
	pass

def on_close(ws):
	print("### closed ###")

def run(*args):
	time.sleep(3)
	for i in range(3):
		time.sleep(1)
		demandResource(str(i))
	time.sleep(3)
	for i in range(3):
		time.sleep(1)
		releaseResource(str(i))
		
def demandResource(resource):
	write_message({"type":"demand_resource","resource":resource,"client_id" : myId})
	lock = threading.Lock()
        lock.acquire()
	resources[resource] = {"lock":lock,"release_key":""}
        return resources[resource]

def releaseResource(resource):
	write_message({"type":"release_resource","resource":resource,"client_id" : myId , "release_key" : resources[resource]["release_key"]})
	if resource in resources :
		del resources[resource] 

if __name__ == "__main__":
	thread.start_new_thread(run, ())
	websocket.enableTrace(True)
	host = "ws://127.0.0.1:9191/central_locking"
	ws = websocket.WebSocketApp(host,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
	ws.run_forever()
