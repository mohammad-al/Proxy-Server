def parse_request(request_bytes):
	"""
	Reads and parses a HTTP request
	param request_bytes (bytes): The bytes of the HTTP request being made
	return: the method, url, and version of HTTP request and the headers
		of the request
	"""
	request_lines = request_bytes.decode().split("\r\n")
	method, url, version = request_lines[0].split()
	headers = request_lines[1:]
	return method, url, version, headers

def extract_host_and_path(url):
	"""
	Extracts the host and path of a request from the url
	param url (str): The url of the request
	return: the host of the url, and the path of the request
	"""
	url_without_http = url.replace("http://", "")

	# Split only once
	host_and_path = url_without_http.split('/', 1)
	host = host_and_path[0]
	path = "/" if len(host_and_path) == 1 else "/" + host_and_path[1]

	return host, path

def build_forward_request(method, path, version, headers, body):
	"""
	Builds the request to be forwarded from the proxy to the server
	param method (str): The HTTP method of the request (GET, POST, PUT, ...)
	param path (str): The path of the request (e.g. /index.html/id=5)
	param version (str): The HTTP request version (usually 1.1)
	param headers (str): The headers of the HTTP request
	param body (bytes): The body of the HTTP request
	return: The request to the proxy server built and encoded
	"""
	# Replace Connection: keep-alive with Connection: close
	filtered_headers = []
	for header_line in headers:
		if header_line.lower().startswith("connection:"):
			filtered_headers.append("Connection: close")
		else:
			filtered_headers.append(header_line)

	request_line = f"{method} {path} {version}\r\n"
	filtered_headers = "\r\n".join(filtered_headers) + "\r\n\r\n"
	return (request_line + filtered_headers + "\r\n\r\n").encode() + body

def get_connection_type(headers):
	"""
	Gets the connection type from the headers such as Keep-alive or close
	param headers (str): The headers where the connection type is
	return: The connection type from the headers
	"""
	for line in headers:
		if line.lower().startswith("connection:"):
			connection_type = line.split(":")[1]	
			return connection_type

	return None

def read_request_body(headers, leftover, socket):
	"""
	Reads the body of a request from client
	param headers (bytes): The headers of the request
	param leftover (bytes): Any bytes from body that may have been already read
	param socket (socket.socket): The client socket
	return: The body of the request, encoded as bytes
	"""
	headers = headers.decode().split("\r\n")
	body = b""
	for line in headers:
		if "Transfer-Encoding: chunked" in line:
			body = read_chunked_body(leftover, socket)
		elif "Content-Length:" in line:
			content_length = int(line.split(": ")[1])
			body = read_body_with_length(content_length - len(leftover), socket)

	return body
	

def read_body_with_length(length, socket):
	"""
	Reads the number of bytes specified from the socket
	param length (int): The number of bytes to read
	param socket (socket.socket): The socket to read from
	return: The data (length num of bytes) that was read from the socket
	"""
	remaining = length 
	data = b""
	while remaining > 0:
		chunk = socket.recv(1024)
		if not chunk:
			raise Exception("Server closed unexpectedly!")
		remaining -= len(chunk)	

	return data

def read_chunked_body(leftover, socket):	
	"""
	Reads body from socket that is chunked
	param leftover (bytes): Any bytes from body that may have already been read
	socket (socket.socket): The client socket where the body is coming from
	"""

	body = b""
	# Buffer is where any recieved data from socket will be stored and read from
	buffer = leftover

	while True:

		# Means we don't have a chunk size to read. Fill buffer till we do
		while b"\r\n" not in buffer:
			buffer += socket.recv(1024)
		
		line, buffer = buffer.split(b"\r\n", 1)
		chunk_size = int(line.decode(), 16)

		# Add the encoded chunk-size and \r\n to data
		body += line + b"\r\n"

		if chunk_size == 0:
			# Add the trailing \r\n to mark end of data
			body += b"\r\n"
			break


		# Means we need to fetch more data from socket to be able
		# to read the full chunk
		while len(buffer) < chunk_size + 2:
			buffer += socket.recv(1024)

		body += buffer[:chunk_size + 2]
		# Update the buffer to start at the next chunk. +2 to skip \r\n
		buffer = buffer[chunk_size + 2:]

	return body
