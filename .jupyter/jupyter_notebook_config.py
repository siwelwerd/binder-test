#Allows for file uploads up to 100MB
c.NotebookApp.tornado_settings = {"websocket_max_message_size": 100 * 1024 * 1024}