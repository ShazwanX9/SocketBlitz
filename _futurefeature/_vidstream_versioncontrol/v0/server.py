import socket
import cv2
import pickle
import struct

# Server configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8080

# Create socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind socket to address and port
server_socket.bind((HOST, PORT))

# Start listening
server_socket.listen(5)
print(f"Server listening on {HOST}:{PORT}...")

# Accept connection from client
client_socket, addr = server_socket.accept()
print(f"Connection established from: {addr}")

# Open the default camera (usually 0)
cap = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    # Serialize frame
    data = pickle.dumps(frame)

    # Send frame size
    client_socket.sendall(struct.pack("L", len(data)))

    # Send frame data
    client_socket.sendall(data)

# Release the camera and close the connection
cap.release()
client_socket.close()
server_socket.close()
