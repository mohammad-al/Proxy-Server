import re
import select
import socket

def read_headers(socket):
	"""
	Reads the headers from a HTTP response
	param socket (socket.socket): The socket connected to client to read
		the HTTP headers from
	return: The HTTP headers, and any part of the body that may have been
		read after the header
	"""
	data = b""
	while b"\r\n\r\n" not in data:
		chunk = socket.recv(4096)
		
		# Client closed the request. No forwarding required
		if not chunk:
			return None, None
		data += chunk


	header_end = data.index(b"\r\n\r\n") + 4
	headers = data[:header_end]
	leftover = data[header_end:]
	return headers, leftover


def handle_connect_method(client_socket, url):
	"""
	Given a client socket and a server url, opens a tunnel between the two
	param client_socket (socket.socket): The client's socket where req from
	param url (str): The server url that client wants to connect to
	return: None
	"""

	host, port = url.split(":")
	port = int(port)

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.connect((host, port))


	# Tell the client that the tunnel is ready
	client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

	client_ip, client_port = client_socket.getpeername()
	print(f"Opening tunnel from {client_ip}:{client_port} to {host}:{port}")

	while True:

		# Monitor the client and server socket for read events
		read_list, _, _ = select.select([client_socket, server_socket], [], [])
		for ready_to_read_socket in read_list:
			data = ready_to_read_socket.recv(4096)

			# Means one of the sockets closed the connection
			if not data:
				client_socket.close()
				server_socket.close()
				return

			# Means client_socket is expecting to read data. Need to send.
			if ready_to_read_socket is client_socket:
				server_socket.sendall(data)
			# Means server_socket is expecting to read data.
			else:
				client_socket.sendall(data)
	
