#!/usr/bin/env python3

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import paho.mqtt.client as mqtt_client
import threading

##
# Wrapper of the MQTT Client
##
class MQTTClient(mqtt_client.Client):
	lock = threading.Lock()
	topics = {}

	# Constructor @see mqtt_client.Client constructor for further informations
	def __init__(self, client_id="", clean_session=None, userdata=None, protocol=mqtt_client.MQTTv311, transport="tcp", reconnect_on_failure=True):
		super().__init__(client_id, clean_session, userdata, protocol, transport, reconnect_on_failure)

	# Add data to specific topic
	# @param topic the topic name
	# @param data the data to save
	def add_topic_data(self, topic, data):
		self.lock.acquire()
		self.topics[topic] = data
		self.lock.release()

	# Pop data corresponding to the wildcard
	# @param wildcard the wildcard
	# @return a list of [TOPIC, DATA, QOS, RETAIN]
	def pop_topic_data(self, wildcard):
		self.lock.acquire()
		res = []
		topics_copy = self.topics.copy()
		for topic in topics_copy:
			if self.wildcard_check(topic, wildcard):
				data = [topic]
				data.extend(self.topics[topic])
				res.append(data)
				del self.topics[topic]
		self.lock.release()
		return res

	# Return True if the given topic match the given wildcard
	# @return True if the given topic match
	def wildcard_check(self, topic, wildcard):
		if wildcard == topic:
			return True
		elif wildcard == '#':
			return True

		res = []
		t = topic.split('/')
		w = wildcard.split('/')

		# Remove empty elements
		t = list(filter(lambda a: a != '', t))
		w = list(filter(lambda a: a != '', w))

		for i in range(len(w)):
			if i > len(t) - 1:
				break
			if w[i] == '+':
				res.append(t[i])
			elif w[i] == '#':
				res.append('/'.join(t[i:]))
				break
			elif w[i] != t[i]:
				break
		return len(res) > 0

# Callback on message received
# @param client the client
# @param userdata 
# @param message the message 
def on_message(client, userdata, message):
	# Get name and data
	client_id = client._client_id.decode('utf-8')
	data = [str(message.payload.decode("utf-8")), message.qos, message.retain]
	# Add data to the client
	clients[client_id].add_topic_data(message.topic, data)

# Init server
app = Flask(__name__)
CORS(app)

# Clients
clients = {}

# Connect route
# @param client client ID
# @param host the broker host
# @param port the broker port (default 1883)
# @param clean_session if true set as a new session (default True)
# @param keep_alive the keep alive in s (default 60)
# @return RC
@app.route("/v1/connect", methods=['GET'])
def connect():
	try:
		# Get data from the client
		client_id = request.args.get('client')
		host = request.args.get('host')

		port = request.args.get('port')
		port = int(port) if port != None else 1883
		
		clean_session = request.args.get('clean_session')
		clean_session = (clean_session.lower() != "false") if clean_session != None else True

		keep_alive = request.args.get('keep_alive')
		keep_alive = int(keep_alive) if keep_alive != None else 60
		
		# Create MQTT Client
		client = MQTTClient(client_id, clean_session)

		# Connect to the broker
		rc = client.connect(host, port, keep_alive)
		if rc != 0:
			resp = jsonify(rc)
			resp.status_code = 400
			return resp

		# Add callback and start main loop
		client.on_message = on_message
		client.loop_start()
		clients[client_id] = client

		# Return OK (RC=0)
		resp = jsonify(0) # ERR_SUCCESS
		resp.status_code = 200
		return resp

	# Internal error
	except ValueError as error:
		resp = jsonify("Connect failed: " + error)
		resp.status_code = 500
		return resp


# Disconnect route
# @param client client ID
# @return RC
@app.route("/v1/disconnect", methods=['GET'])
def disconnect():
	try:
		# Get the client
		client = request.args.get('client')
		if client in clients:
			# Disconnect
			mqtt_client = clients[client]
			rc = mqtt_client.disconnect()
			mqtt_client.loop_stop() # MQTT_ERR_INVAL (if the thread does not exists) is ignored here 
			del clients[client]

			# If RC!=0 return 400
			resp = jsonify(rc)
			if rc != 0:
				resp.status_code = 400
			else:
				resp.status_code = 200
		
		# Client not found
		else:
			resp = jsonify(4) # ERR_NO_CONN
			resp.status_code = 400
		
		# Return response
		return resp

	# Internal error
	except ValueError as error:
		resp = jsonify("Disconnect failed: " + error)
		resp.status_code = 500
		return resp


# Subscribe route
# @param client client ID
# @param topic the topic
# @param qos the QoS (default 0)
# @return [RC, Message ID]
@app.route("/v1/subscribe", methods=['GET'])
def subscribe():
	try:
		# Get the client
		client = request.args.get('client')
		if client in clients:

			# Get other client values
			topic = request.args.get('topic')
			qos = request.args.get('qos')
			qos = int(qos) if qos != None else 0

			# Convert * to #
			topic = topic.replace('*', '#')

			# Subscribe
			rc, mid = clients[client].subscribe(topic, qos)

			# If RC!=0 return 400
			resp = jsonify([rc, mid])
			if rc != 0:
				resp.status_code = 400
			else:
				resp.status_code = 200
		# Client not found
		else:
			resp = jsonify([4, None]) # ERR_NO_CONN
			resp.status_code = 400
		
		# Return response
		return resp

	# Internal error
	except ValueError as error:
		resp = jsonify("Subscribe failed: " + error)
		resp.status_code = 500
		return resp


# Unsubscribe route
# @param client client ID
# @param topic the topic
# @return [RC, Message ID]
@app.route("/v1/unsubscribe", methods=['GET'])
def unsubscribe():
	try:
		# Get the client
		client = request.args.get('client')
		if client in clients:

			# Get other client values
			topic = request.args.get('topic')
			# Convert * to #
			topic = topic.replace('*', '#')


			# Subscribe
			rc, mid = clients[client].unsubscribe(topic)

			# If RC!=0 return 400
			resp = jsonify([rc, mid])
			if rc != 0:
				resp.status_code = 400
			else:
				resp.status_code = 200
		# Client not found
		else:
			resp = jsonify([4, None]) # ERR_NO_CONN
			resp.status_code = 400
		
		# Return response
		return resp

	# Internal error
	except ValueError as error:
		resp = jsonify("Unsubscribe failed: " + error)
		resp.status_code = 500
		return resp


# Publish route
# @param client client ID
# @param topic the topic
# @param value the value to publish
# @param qos the QoS (default 0)
# @param retain if True, retain the message (default False)
# @return [RC, Message ID]
@app.route("/v1/publish", methods=['GET'])
def publish():
	try:
		# Get the client
		client = request.args.get('client')
		if client in clients:

			# Get other client values
			topic = request.args.get('topic')
			data = request.args.get('value')

			qos = request.args.get('qos')
			qos = int(qos) if qos != None else 0

			retain = request.args.get('retain')
			retain = (retain.lower() != "false") if retain != None else False

			# Convert * to #
			topic = topic.replace('*', '#')


			# Publish
			rc, mid = clients[client].publish(topic, data, qos, retain)
			
			# If RC!=0 return 400
			resp = jsonify([rc, mid])
			if rc != 0:
				resp.status_code = 400
			else:
				resp.status_code = 200
		# Client not found
		else:
			resp = jsonify([4, None]) # ERR_NO_CONN
			resp.status_code = 400
		
		# Return response
		return resp

	# Internal error
	except ValueError as error:
		resp = jsonify("Publish failed: " + error)
		resp.status_code = 500
		return resp


# Get data route
# @param client client ID
# @param topic the topic
# @return data as a list of [TOPIC, DATA, QOS, RETAIN]
@app.route("/v1/get", methods=['GET'])
def get():
	# Get the client
	client = request.args.get('client')
	if client in clients:

		# Get other client values
		topic = request.args.get('topic')
		# Convert * to #
		topic = topic.replace('*', '#')

		data = clients[client].pop_topic_data(topic)
		resp = jsonify(data)
		if len(data) > 0:
			resp.status_code = 200
		else:
			resp.status_code = 204

		return resp

	# Client not found
	else:
		resp = jsonify(4) # ERR_NO_CONN
		resp.status_code = 400
	return resp
