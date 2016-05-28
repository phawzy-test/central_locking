import websocket
import json

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.create_connection("ws://127.0.0.1:9191/central_locking")
    print("Sending 'Hello, World'...")
    ws.send(json.dumps({""}))
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print("Received {}".format(result))
    ws.close()