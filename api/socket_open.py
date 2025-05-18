import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
hostname = socket.gethostname()
print(hostname)
hostname = "127.0.0.1"
sock.bind((hostname, 8080))
print("socket opened")

while True:
    try:
        continue
    except KeyboardInterrupt:
        break


sock.close()
print("socked closed")
