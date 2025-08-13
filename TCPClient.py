import socket

HOST = '127.0.0.1'
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.sendall("Xin chào server".encode())

data = client.recv(1024).decode()
print("Server trả lời:", data)

client.close()