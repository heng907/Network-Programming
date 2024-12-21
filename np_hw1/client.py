import socket

# 發送遊戲邀請 (UDP)
def send_game_invitation(server_ip, server_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    invitation_message = "Game invitation"
    udp_socket.sendto(invitation_message.encode(), (server_ip, server_port))
    
    response, _ = udp_socket.recvfrom(1024)
    if response.decode() == "Accepted":
        print(f"Server {server_ip} accepted the invitation")
        tcp_port, _ = udp_socket.recvfrom(1024)
        print(f"TCP port for game: {tcp_port.decode()}")
        udp_socket.close()
        return int(tcp_port.decode())
    else:
        print(f"Server {server_ip} declined the invitation")
    udp_socket.close()
    return None

# 加入遊戲 (TCP)
def join_game_server(server_ip, tcp_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_ip, tcp_port))
    print(f"Connected to server {server_ip}:{tcp_port}")
    
    while True:
        player_move = input("Your move (rock, paper, scissors): ").strip().lower()
        tcp_socket.send(player_move.encode())
        if player_move == "exit":
            break
        
        server_move = tcp_socket.recv(1024).decode()
        print(f"Server move: {server_move}")
        
        if player_move == server_move:
            print("It's a tie!")
        elif (player_move == "rock" and server_move == "scissors") or \
             (player_move == "scissors" and server_move == "paper") or \
             (player_move == "paper" and server_move == "rock"):
            print("You win!")
        else:
            print("Server wins!")
    
    tcp_socket.close()

if __name__ == "__main__":
    server_ip = "140.113.235.151" # 學校IP
    # server_ip = "140.113.235.152"
    # server_ip = "140.113.235.153"
    # server_ip = "140.113.235.154"
    # server_ip = "127.0.0.1"  # 本地測試時使用 localhost
    udp_port = 10001  # 發送邀請的 UDP 端口
    tcp_port = 50000  # 接收邀請時獲得的 TCP 端口
    # 首先發送遊戲邀請，並獲取 TCP 端口
    tcp_port = send_game_invitation(server_ip, udp_port)
    
    # 如果伺服器接受邀請，則加入遊戲
    if tcp_port:
        join_game_server(server_ip, tcp_port)
    else:
        print("Failed to join the game.")
