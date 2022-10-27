# RESQTT
Proxy REST MQTT (REpresentational State Queuing Telemetry Transport)

To run it
```
pip install flask
FLASK_APP=RESQTT.py flask run
```

The API
- **/v1/connect (GET)**: Connect to the MQTT broker
- **/v1/disconnect (GET)**: Disconnect to the MQTT broker
- **/v1/subscribe (GET)**: Subscribe to a specific topic
- **/v1/unsubscribe (GET)**: Unsubscribe to a specific topic
- **/v1/publish (GET)**: Publish to a specific topic
- **/v1/get (GET)**: Get the last data received of the specific topic

The wildcard # is replaced by *

Some examples
```
http://127.0.0.1:5000/v1/connect?client=my_client&host=127.0.0.1&keep_alive=45 # Return RC

http://127.0.0.1:5000/v1/subscribe?client=my_client&topic=my_topic
http://127.0.0.1:5000/v1/get?client=my_client&topic=my_topic
http://127.0.0.1:5000/v1/unsubscribe?client=my_client&topic=my_topic

http://127.0.0.1:5000/v1/publish?client=my_client&topic=my_topic&data=my_data #

http://127.0.0.1:5000/v1/subscribe?client=my_client&topic=*
http://127.0.0.1:5000/v1/get?client=my_client&topic=my_other_topic
http://127.0.0.1:5000/v1/get?client=my_client&topic=*
http://127.0.0.1:5000/v1/unsubscribe?client=my_client&topic=*

http://127.0.0.1:5000/v1/disconnect?client=my_client
```
