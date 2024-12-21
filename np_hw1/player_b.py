import socket

# open the udp server
def start_udp_server(udp_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', udp_port))
    print(f"Listening for invitations on UDP port {udp_port}...")

    while True:
        message, addr = udp_socket.recvfrom(1024)
        message = message.decode()

        if message == "Are you available?":
            # reply player a
            udp_socket.sendto(b"Waiting for invitation", addr)
            print(f"Received availability check from {addr[0]}")
        elif message == "Game invitation":
            print(f"Received invitation from {addr[0]}")

            # palyer b to choose to accept or deny
            accept = input("Do you accept the invitation? (y/n): ").strip().lower()
            if accept == 'y':
                udp_socket.sendto(b"Accepted", addr)
                print("Waiting for Player A's TCP port...")

                # get the tcp port num from player a
                tcp_port_data, _ = udp_socket.recvfrom(1024)
                tcp_port = int(tcp_port_data.decode())
                print(f"Received TCP port: {tcp_port}. Connecting to Player A...")
                udp_socket.close()
                connect_to_game(addr[0], tcp_port)
                break
            else:
                udp_socket.sendto(b"Declined", addr)
                print("Invitation declined. Waiting for other invitations...")
        else:
            print(f"Received unknown message from {addr[0]}: {message}")

# use the player a tcp port
def connect_to_game(server_ip, tcp_port):
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, tcp_port))
        print(f"Connected to Player A at {server_ip}:{tcp_port}")

        play_game(tcp_socket)

        tcp_socket.close()
    except Exception as e:
        print(f"Error connecting to Player A: {e}")

# gmaing
def play_game(tcp_socket):
    valid_moves = ["rock", "paper", "scissors", "exit"]
    while True:
        move = input("Your move (rock, paper, scissors, or exit): ").strip().lower()
        if move not in valid_moves:
            print("Invalid move. Please try again.")
            continue

        tcp_socket.send(move.encode())
        if move == "exit":
            print("Exiting game.")
            break

        server_move = tcp_socket.recv(1024).decode()
        # print(f"Player A's move: {server_move}")

        # judge
        if server_move == "exit":
            print("Player A exited the game.")
            break
        elif move == server_move:
            print("It's a tie!")
        elif (move == "rock" and server_move == "scissors") or \
             (move == "scissors" and server_move == "paper") or \
             (move == "paper" and server_move == "rock"):
            print("You win!")
        else:
            print("Player A wins!")

if __name__ == "__main__":
    udp_port = int(input("Enter the UDP port to listen on (16000-16010): "))
    start_udp_server(udp_port)
