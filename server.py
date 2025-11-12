#!/usr/bin/env python3
# ultra simple chat server (IRC-like, minimal)

import socket
import threading

HOST = "0.0.0.0"
PORT = 12345

clients = {}  # sock -> (addr, nick)
lock = threading.Lock()

def broadcast(text, exclude_sock=None):
    with lock:
        for sock in list(clients.keys()):
            if sock is exclude_sock:
                continue
            try:
                sock.sendall(text.encode('utf-8') + b'\n')
            except Exception:
                remove_client(sock)

def send_to(sock, text):
    try:
        sock.sendall(text.encode('utf-8') + b'\n')
    except Exception:
        remove_client(sock)

def remove_client(sock):
    with lock:
        if sock in clients:
            addr, nick = clients.pop(sock)
            try:
                sock.close()
            except:
                pass
            broadcast(f"*** {nick} disconnected")

def handle_client(sock, addr):
    try:
        send_to(sock, "Welcome! Please set your nickname with: /nick YOUR_NAME")
        buff = sock.recv(4096).decode('utf-8', errors='ignore').strip()
        # wait until nick is provided
        nick = None
        while True:
            if not buff:
                remove_client(sock)
                return
            if buff.startswith('/nick '):
                nick = buff.split(' ', 1)[1].strip() or f"user{addr[1]}"
                with lock:
                    # ensure uniqueness
                    existing = {n for (_, n) in clients.values()}
                    if nick in existing:
                        send_to(sock, f"*** Nick '{nick}' is taken, choose another.")
                        send_to(sock, "Try: /nick NEWNAME")
                        buff = sock.recv(4096).decode('utf-8', errors='ignore').strip()
                        continue
                    clients[sock] = (addr, nick)
                break
            else:
                send_to(sock, "Please set nickname first: /nick YOUR_NAME")
                buff = sock.recv(4096).decode('utf-8', errors='ignore').strip()

        broadcast(f"*** {nick} joined the chat")
        send_to(sock, "*** Type /help for commands")

        while True:
            data = sock.recv(4096).decode('utf-8', errors='ignore')
            if not data:
                break
            for line in data.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith('/'):
                    # command
                    parts = line.split(' ', 2)
                    cmd = parts[0].lower()
                    if cmd == '/quit':
                        send_to(sock, "*** Bye!")
                        remove_client(sock)
                        return
                    elif cmd == '/nick':
                        if len(parts) >= 2:
                            newnick = parts[1].strip()
                            with lock:
                                existing = {n for (_, n) in clients.values()}
                                if newnick in existing:
                                    send_to(sock, f"*** Nick '{newnick}' is taken.")
                                else:
                                    old = clients[sock][1]
                                    clients[sock] = (addr, newnick)
                                    broadcast(f"*** {old} is now known as {newnick}")
                        else:
                            send_to(sock, "*** Usage: /nick NEWNAME")
                    elif cmd == '/list':
                        with lock:
                            nicks = [n for (_, n) in clients.values()]
                        send_to(sock, "*** Users: " + ", ".join(nicks))
                    elif cmd == '/msg':
                        # /msg target message...
                        if len(parts) >= 3:
                            target = parts[1].strip()
                            msg = parts[2].strip()
                            sent = False
                            with lock:
                                for s, (_, n) in clients.items():
                                    if n == target:
                                        send_to(s, f"[PM from {clients[sock][1]}] {msg}")
                                        sent = True
                                        break
                            if sent:
                                send_to(sock, f"[PM to {target}] {msg}")
                            else:
                                send_to(sock, f"*** No such user: {target}")
                        else:
                            send_to(sock, "*** Usage: /msg USERNAME message")
                    elif cmd == '/help':
                        send_to(sock, "*** Commands: /nick NAME | /list | /msg USER TEXT | /quit | /help")
                    else:
                        send_to(sock, f"*** Unknown command: {cmd}. Type /help")
                else:
                    # broadcast message
                    nick = clients.get(sock, ("", "unknown"))[1]
                    broadcast(f"<{nick}> {line}", exclude_sock=None)
    except Exception as e:
        #print("Client handler error:", e)
        pass
    finally:
        remove_client(sock)

def accept_loop(server_sock):
    while True:
        try:
            sock, addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(sock, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            break
        except Exception:
            continue

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        accept_loop(s)

if __name__ == '__main__':
    main()
