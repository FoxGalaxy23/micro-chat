#!/usr/bin/env python3
# ultra simple chat client

import socket
import threading
import sys

if len(sys.argv) < 3:
    print("Usage: python client.py HOST PORT")
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

def recv_loop(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("*** Disconnected from server")
                break
            for line in data.decode('utf-8', errors='ignore').splitlines():
                print(line)
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except:
            pass
        sys.exit(0)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            line = input()
            if not line:
                continue
            # send line to server
            try:
                sock.sendall(line.encode('utf-8') + b'\n')
            except Exception:
                print("*** Failed to send, exiting")
                break
            if line.strip().lower() == '/quit':
                break
    except KeyboardInterrupt:
        try:
            sock.sendall(b'/quit\n')
        except:
            pass
    finally:
        sock.close()

if __name__ == '__main__':
    main()
