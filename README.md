# central_locking
websocket api for demanding resources

1-run python server.py

2-access localhost:9191

3-demand resources and release it as much as you want through web ui



p.s. you can implement your own websocket client in any language

-currently implementing a python client

central locking system : 

	1-exclusive access on shared resources
	
	2-demand resources and release them
	
	3-access queue for waiting clients
	
	4-detect simple deadlocks(not chainedeadlocks) but doesn't handle them 
	
	5-you can implement handleDeadlock function that's called after detecting any deadlock
	
	6-support timeout for cuurent resource holder or any of the access queue
