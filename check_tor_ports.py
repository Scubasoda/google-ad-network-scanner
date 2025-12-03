import socket

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

ports = [9050, 9150]
for port in ports:
    if check_port(port):
        print(f"Port {port} is OPEN (Tor likely running)")
    else:
        print(f"Port {port} is CLOSED")
