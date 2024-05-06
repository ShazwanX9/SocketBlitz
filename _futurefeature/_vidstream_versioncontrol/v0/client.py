import socket
import cv2
import pickle
import struct
import threading

# Server configuration
HOST = '127.0.0.1'  # Server IP address
PORT = 8080

# Create socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((HOST, PORT))

data = b""
payload_size = struct.calcsize("L")

# Open a video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('received_video.avi', fourcc, 20.0, (640, 480))

frame = None

def display():
    global frame
    while True:
        if frame is not None:
            print("Displaying frame...")
            cv2.imshow("Display window", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                break
    cv2.destroyAllWindows()

threading.Thread(target=display).start()

while True:
    # Receive frame size
    while len(data) < payload_size:
        data += client_socket.recv(4096)

    # Extract frame size
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    # Receive frame data
    while len(data) < msg_size:
        data += client_socket.recv(4096)

    # Extract frame data
    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserialize frame
    frame = pickle.loads(frame_data)

    # # Write frame to video file
    # out.write(frame)

# Release video writer and close connection
out.release()
client_socket.close()
