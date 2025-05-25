import socket

def start_mock_server(host: str, port: int):
    """
    Start a mock TCP server that implements the 4-packet image protocol:
      - For each image:
          * Receive 4 × 1024 B packets
          * After packets 1–3, send a single-byte ACK (0x01)
          * After packet 4, send a 4-byte LE integer result (0)
      - When a client disconnects, go back to listening for the next one
    """
    # Set up listening socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)
        print(f"[+] Mock server listening on {host}:{port}")
        
        while True:
            conn, addr = srv.accept()
            print(f"[+] Connection from {addr}")
            with conn:
                try:
                    while True:
                        # Receive one “image” = 4 × 1024-byte packets
                        for i in range(4):
                            buf = b''
                            while len(buf) < 1024:
                                chunk = conn.recv(1024 - len(buf))
                                if not chunk:
                                    # Client closed mid-image
                                    raise ConnectionResetError()
                                buf += chunk
                            print(f"    • Received packet {i+1} ({len(buf)} bytes)")
                            
                            # ACK for packets 1–3
                            if i < 3:
                                conn.sendall(b'\x01')
                        
                        # Send a dummy classification result (always 0)
                        result = 0
                        result_bytes = result.to_bytes(4, byteorder='little', signed=False)
                        conn.sendall(result_bytes)
                        print("    • Sent classification result =", result)
                
                except (ConnectionResetError, BrokenPipeError):
                    print("[*] Client disconnected, waiting for next connection...\n")
                except Exception as e:
                    print("[!] Server error:", e, "\n[*] Waiting for next connection...\n")

if __name__ == "__main__":
    # listen on all interfaces, port 7 by default to match your client
    start_mock_server("0.0.0.0", 7)
