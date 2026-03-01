import socket
import threading
from request_response import *
from requests import *
from responses import *

HOST = "127.0.0.1"
PORT = 65000

def forward_request(request, body):

	method, url, version, request_headers = parse_request(request)
	connection_type = get_connection_type(request_headers)
	host, path = extract_host_and_path(url)
	forward_data = build_forward_request(method, path, version, request_headers, body)

	# Create another socket to connect to the server
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:

		server_socket.connect((host, 80))

		print()
		print("Making request to server...")
		print(f"Method: {method}\nHost: {host}\nPath: {path}\nVersion: {version}")
		server_socket.sendall(forward_data)
		print("Request sent")
		print()

		server_response = get_response(server_socket)
		server_response = change_connection_type(server_response, connection_type)
		return server_response

def handle_client(client_socket):

	while True:
		headers, leftover = read_headers(client_socket)
		if headers is None:
			break

		method, url,_ ,_= parse_request(headers)
		if method == "CONNECT":
			handle_connect_method(client_socket, url) 	
			break
		else:
			body = read_request_body(headers, leftover, client_socket)
			response = forward_request(headers, body)
			client_socket.sendall(response)

	client_socket.close()


def main():
	# AF_INET uses IPv4 address family. SOCK_STREAM uses TCP
	listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# Allow reuse of port
	listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	
	listening_socket.bind((HOST, PORT))
	listening_socket.listen()
	
	print(f"Listening on {(HOST, PORT)}")
	
	try:
		# This while loop handles each client
		while True:

			client_socket, addr = listening_socket.accept()
			client_ip, client_addr = addr
			print(f"Accepted connection from {client_ip} {client_addr}")

			client_thread = threading.Thread(target=handle_client, args=(client_socket,))
			client_thread.daemon = True
			client_thread.start()
			print(f"Closing connection from {client_ip} {client_addr}.")
	except KeyboardInterrupt:
		print()
		print(f"Shutting down proxy server...")
	
if __name__ == "__main__":
	main()
