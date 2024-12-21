import socket

# 接收遊戲邀請 (UDP)
def receive_game_invitation(udp_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', udp_port))  # 綁定到 UDP 端口
    print(f"Waiting for game invitations on UDP port {udp_port}...")

    while True:
        message, addr = udp_socket.recvfrom(1024)
        print(f"Received invitation from {addr}")

        # 接受遊戲邀請
        accept = input("Accept invitation? (yes/no): ").strip().lower()
        if accept == "yes":
            udp_socket.sendto(b"Accepted", addr)
            tcp_port = 50000  # 使用固定的 TCP 端口
            udp_socket.sendto(str(tcp_port).encode(), addr)  # 發送 TCP 端口號給客戶端
            print(f"Starting TCP server on port {tcp_port}...")  # Debug 訊息
            start_game_server(tcp_port)  # 開啟 TCP 伺服器
        else:
            udp_socket.sendto(b"Declined", addr)

# 遊戲過程 (TCP)
def start_game_server(tcp_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen(1)
    print(f"TCP server is listening on port {tcp_port}...")
    
    conn, addr = tcp_socket.accept()
    print(f"Player connected from {addr}")
    
    while True:
        player_move = conn.recv(1024).decode()
        if player_move == "exit":
            print("Player exited the game.")
            break
        
        server_move = input("Your move (rock, paper, scissors): ").strip().lower()
        conn.send(server_move.encode())
        
        if player_move == server_move:
            print("It's a tie!")
        elif (server_move == "rock" and player_move == "scissors") or \
             (server_move == "scissors" and player_move == "paper") or \
             (server_move == "paper" and player_move == "rock"):
            print("You win!")
        else:
            print("Player wins!")
    
    conn.close()
    tcp_socket.close()

if __name__ == "__main__":
    udp_port = 10001  # 假設 UDP 端口
    receive_game_invitation(udp_port)
    tcp_port = 50000  # 假設 TCP 端口
    start_game_server(tcp_port)
