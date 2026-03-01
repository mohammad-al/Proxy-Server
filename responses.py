from request_response import read_headers

def get_response(socket):
	"""
	Reads the response from a server after request has been made
	param socket (socket.socket): The socket connected to server to read
		response from.
	"""
	response_headers, response_leftover = read_headers(socket)

	response_body = response_leftover
	while True:
		chunk = socket.recv(8192)
		if not chunk:
			break

		response_body += chunk

	return response_headers + response_body


def change_connection_type(response, connection_type):
	"""
	Changes the connection header in response to the connection type given
	param connection_type (str): The connection type e.g. keep-alive
	return: The response with the connection header changed to connection_type
	"""

	headers, body = response.split(b"\r\n\r\n", 1)
	headers = headers.decode().split("\r\n")
	new_headers = []

	for line in headers:
		if line.lower().startswith("connection:"):
			new_headers.append(f"Connection:{connection_type}")
		else:
			new_headers.append(line)

	# If no connection type in headers, add one
	if not any(line.lower().startswith("connection:") for line in headers):
		new_headers.append("Connection:{connection_type}")

	result = "\r\n".join(new_headers).encode() + b"\r\n\r\n" + body
	return result
			
		
