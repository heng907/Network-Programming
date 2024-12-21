import socket
import random

# school server IP
SERVER_IPS = ['140.113.235.151', '140.113.235.152', '140.113.235.153', '140.113.235.154']
UDP_PORT_RANGE = range(16000, 16011)

# search palyer
def find_available_players():
    available_players = []
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(0.5)  # avoid wait for long 

    for ip in SERVER_IPS:
        for port in UDP_PORT_RANGE:
            try:
                message = "Are you available?"
                udp_socket.sendto(message.encode(), (ip, port))
                response, addr = udp_socket.recvfrom(1024)
                if response.decode() == "Waiting for invitation":
                    print(f"Found player at {ip}:{port}")
                    available_players.append((ip, port))
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error contacting {ip}:{port} - {e}")
                continue

    udp_socket.close()
    return available_players

# sent invitaion (UDP)
def send_game_invitation(server_ip, server_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(5)

    try:
        # game invitaion
        udp_socket.sendto(b"Game invitation", (server_ip, server_port))
        print(f"\nInvitation sent to {server_ip}:{server_port}. Waiting for Player B to accept...")

        response, _ = udp_socket.recvfrom(1024)
        if response.decode() == "Accepted":
            print("Player B accepted the invitation.")

            # send TCP port to player b
            tcp_port = random.randint(16000, 16010)
            print(f"Selected TCP port: {tcp_port}")
            udp_socket.sendto(str(tcp_port).encode(), (server_ip, server_port))
            print(f"Sent TCP port {tcp_port} to Player B.")
            udp_socket.close()
            start_tcp_server(tcp_port)  # open the tcp server
        else:
            print("Player B declined the invitation.")
            udp_socket.close()
    except socket.timeout:
        print("No response from Player B.")
        udp_socket.close()

# wait for tcp server
def start_tcp_server(tcp_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen(1)
    print(f"TCP server started on port {tcp_port}. Waiting for Player B...")

    conn, addr = tcp_socket.accept()
    print(f"Player B connected from {addr}!")

    play_game(conn)

    conn.close()
    tcp_socket.close()

# game
def play_game(conn):
    valid_moves = ["rock", "paper", "scissors", "exit"]
    while True:
        player_move = conn.recv(1024).decode()
        if player_move == "exit":
            print("Player B exited the game.")
            break

        # print(f"Player B's move: {player_move}")
        server_move = input("Your move (rock, paper, scissors): ").strip().lower()
        if server_move not in valid_moves:
            print("Invalid move. Please try again.")
            continue

        conn.send(server_move.encode())

        # judge
        if server_move == player_move:
            print("It's a tie!")
        elif (server_move == "rock" and player_move == "scissors") or \
             (server_move == "scissors" and player_move == "paper") or \
             (server_move == "paper" and player_move == "rock"):
            print("You win!")
        else:
            print("Player B wins!")

if __name__ == "__main__":
    available_players = find_available_players()
    if available_players:
        print("\nAvailable players:")
        for idx, (ip, port) in enumerate(available_players):
            print(f"{idx + 1}. {ip}:{port}")
        choice = int(input("Select a player to invite (enter number): ")) - 1
        selected_ip, selected_port = available_players[choice]
        send_game_invitation(selected_ip, selected_port)
    else:
        print("No available players found.")
