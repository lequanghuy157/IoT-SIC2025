import socket

HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server đang lắng nghe...")

conn, addr = server.accept()
print("Kết nối từ:", addr)

data = conn.recv(1024).decode()
print("Nhận được:", data)

conn.sendall("Đã nhận!".encode())
conn.close()