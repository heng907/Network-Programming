import socket
import json
import random
import threading

def main():
    server_ip = input("Enter lobby server IP: ")
    server_port = int(input("Enter lobby server port (16000-16010): "))

    while True:
        print("\nMain Menu:")
        print("[1] Register")
        print("[2] Login")
        print("[3] Exit")
        option = input("Choose an option: ").strip()
        if option == "1":
            lobby_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                lobby_socket.connect((server_ip, server_port))
                register(lobby_socket)
            except Exception as e:
                print(f"Could not connect to server: {e}")
            finally:
                lobby_socket.close()
        elif option == "2":
            lobby_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                lobby_socket.connect((server_ip, server_port))
                if login(lobby_socket):
                    pass  # Login successful, handled in login function
            except Exception as e:
                print(f"Could not connect to server: {e}")
            finally:
                lobby_socket.close()
        elif option == "3":
            print("Exiting the application.")
            break
        else:
            print("Invalid option. Please try again.")

def register(lobby_socket):
    username = input("Enter username: ")
    password = input("Enter password: ")
    message = {
        "action": "register",
        "username": username,
        "password": password
    }
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(4096).decode()
    if response_data:
        response = json.loads(response_data)
        print(response.get("message", "Registration error"))
    else:
        print("No response from server. Please try again.")

def login(lobby_socket):
    username = input("Enter username: ")
    message = {"action": "login", "username": username}
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(4096).decode()
    if response_data:
        response = json.loads(response_data)
        if response.get("status") == "prompt":
            password = input(response.get("message"))
            lobby_socket.send(password.encode())
            response_data = lobby_socket.recv(4096).decode()
            if response_data:
                response = json.loads(response_data)
                if response.get("status") == "success":
                    print("Login successful!")

                    # Start a thread to listen for invitations
                    threading.Thread(target=listen_for_invitations, args=(lobby_socket,), daemon=True).start()

                    # Display online players
                    online_players = response.get("online_players", {})
                    if len(online_players) == 1 and username in online_players:
                        print("Currently, no players are online.")
                    else:
                        print("Online Players:")
                        for user, status in online_players.items():
                            if user != username and status != "offline":
                                print(f"- {user}: {status}")

                    # Display public rooms
                    rooms = response.get("rooms", {})
                    if not rooms:
                        print("No public rooms waiting for players.")
                    else:
                        print("Public Rooms:")
                        for room_id, room_info in rooms.items():
                            print(f"- Room ID: {room_id}, Creator: {room_info['creator']}, Game Type: {room_info['game_type']}, Status: {room_info['status']}")

                    lobby_menu(lobby_socket, username)
                    return True
                else:
                    print(f"Login failed: {response.get('message')}")
            else:
                print("No response from server after sending password. Please try again.")
        else:
            print(f"Login failed: {response.get('message')}")
    else:
        print("No response from server during login. Please try again.")
    return False

def listen_for_invitations(lobby_socket):
    while True:
        try:
            message = lobby_socket.recv(4096).decode()
            if message:
                data = json.loads(message)
                if data.get("action") == "invite":
                    from_user = data.get("from_user")
                    room_id = data.get("room_id")
                    game_type = data.get("game_type")
                    print(f"\nYou have been invited by {from_user} to join a game room '{room_id}' playing {game_type}.")
                    choice = input("Do you want to accept the invitation? (yes/no): ").strip().lower()
                    response = {
                        "action": "respond_invite",
                        "from_user": from_user,
                        "room_id": room_id,
                        "response": choice
                    }
                    lobby_socket.send(json.dumps(response).encode())
                    if choice == "yes":
                        # Proceed to join the game
                        join_private_room(lobby_socket, room_id)
                    else:
                        print("Invitation declined.")
            else:
                # Server closed the connection
                print("Server connection closed.")
                break
        except Exception as e:
            print(f"Error in listening for invitations: {e}")
            break

def lobby_menu(lobby_socket, username):
    while True:
        print("\nLobby Menu:")
        print("[1] Create Room")
        print("[2] Join Public Room")
        print("[3] Logout")
        option = input("Choose an option: ").strip()
        if option == "1":
            create_room(lobby_socket, username)
        elif option == "2":
            join_public_room(lobby_socket)
        elif option == "3":
            logout(lobby_socket)
            break
        else:
            print("Invalid option. Please try again.")

def create_room(lobby_socket, username):
    room_id = input("Enter room ID for the room: ")
    tcp_port = int(input("Enter TCP port for the game server: "))
    print("Choose a game type:")
    print("(1) Rock-Paper-Scissors")
    print("(2) Guess Number")
    game_choice = input("Enter the number of the game type: ").strip()

    if game_choice == "1":
        game_type = "Rock-Paper-Scissors"
    elif game_choice == "2":
        game_type = "Guess Number"
    else:
        print("Invalid choice. Please try again.")
        return

    print("Choose room type:")
    print("(1) Public Room")
    print("(2) Private Room")
    room_choice = input("Enter the number of the room type: ").strip()

    if room_choice == "1":
        room_type = "public"
    elif room_choice == "2":
        room_type = "private"
    else:
        print("Invalid choice. Please try again.")
        return

    message = {
        "action": "create_room",
        "room_id": room_id,
        "game_type": game_type,
        "room_type": room_type,
        "tcp_port": tcp_port
    }
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(4096).decode()
    if response_data:
        response = json.loads(response_data)
        if response.get("status") == "success":
            print(response.get("message", "Room created successfully."))
            if room_type == "private":
                invite_players(lobby_socket, room_id)
            else:
                print("Waiting for players to join...")
            start_tcp_server(tcp_port, game_type, lobby_socket, room_id)
        else:
            print(response.get("message", "Room creation error"))
    else:
        print("No response from server during room creation. Please try again.")

def invite_players(lobby_socket, room_id):
    while True:
        message = {"action": "get_idle_players"}
        lobby_socket.send(json.dumps(message).encode())
        response_data = lobby_socket.recv(4096).decode()
        if response_data:
            response = json.loads(response_data)
            idle_players = response.get("idle_players", [])
            if not idle_players:
                print("No idle players available to invite.")
                break
            else:
                print("Idle Players:")
                for idx, player in enumerate(idle_players):
                    print(f"{idx+1}. {player}")
                choice = input("Enter the number of the player to invite (or 'done' to finish inviting): ").strip()
                if choice.lower() == "done":
                    break
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(idle_players):
                        invited_player = idle_players[idx]
                        message = {
                            "action": "invite_player",
                            "room_id": room_id,
                            "to_user": invited_player
                        }
                        lobby_socket.send(json.dumps(message).encode())
                        print(f"Invitation sent to {invited_player}.")
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Invalid input. Please try again.")
        else:
            print("No response from server while inviting players. Please try again.")

def join_public_room(lobby_socket):
    room_id = input("Enter public room ID to join: ")
    message = {"action": "join_room", "room_id": room_id}
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(4096).decode()
    if response_data:
        response = json.loads(response_data)
        if response.get("status") == "success":
            game_ip = response.get("game_ip")
            game_port = int(response.get("game_port"))
            game_type = response.get("game_type")
            connect_to_game(game_ip, game_port, game_type, lobby_socket)
        else:
            print(response.get("message", "Room joining error"))
    else:
        print("No response from server during room joining. Please try again.")

def join_private_room(lobby_socket, room_id):
    message = {"action": "join_room", "room_id": room_id}
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(4096).decode()
    if response_data:
        response = json.loads(response_data)
        if response.get("status") == "success":
            game_ip = response.get("game_ip")
            game_port = int(response.get("game_port"))
            game_type = response.get("game_type")
            connect_to_game(game_ip, game_port, game_type, lobby_socket)
        else:
            print(response.get("message", "Room joining error"))
    else:
        print("No response from server during room joining. Please try again.")

def start_tcp_server(tcp_port, game_type, lobby_socket, room_id):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen(1)
    print(f"TCP server started on port {tcp_port}. Waiting for opponent...")

    conn, addr = tcp_socket.accept()
    print(f"Opponent connected from {addr}!")
    if game_type == "Rock-Paper-Scissors":
        play_rps(conn)
    elif game_type == "Guess Number":
        play_guess_the_number(conn)
    conn.close()
    tcp_socket.close()

    # Notify lobby server that game is over and remove room
    message = {"action": "game_over", "room_id": room_id}
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(1024).decode()
    if response_data:
        response = json.loads(response_data)
        print(response.get("message", "Status update error"))
    else:
        print("No response from server during status update. Please try again.")

def connect_to_game(server_ip, tcp_port, game_type, lobby_socket):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_ip, tcp_port))
    print(f"Connected to game server at {server_ip}:{tcp_port}")

    if game_type == "Rock-Paper-Scissors":
        play_rps(tcp_socket)
    elif game_type == "Guess Number":
        play_guess_the_number(tcp_socket)
    tcp_socket.close()

    # Notify lobby server that game is over
    message = {"action": "game_over"}
    lobby_socket.send(json.dumps(message).encode())
    response_data = lobby_socket.recv(1024).decode()
    if response_data:
        response = json.loads(response_data)
        print(response.get("message", "Status update error"))
    else:
        print("No response from server during status update. Please try again.")

def play_rps(conn):
    print("Starting Rock-Paper-Scissors game!")
    valid_moves = ["rock", "paper", "scissors", "exit"]
    while True:
        move = input("Your move (rock, paper, scissors, or exit): ").strip().lower()
        if move not in valid_moves:
            print("Invalid move. Please try again.")
            continue

        conn.send(move.encode())
        if move == "exit":
            print("Exiting game.")
            break

        opponent_move = conn.recv(1024).decode()
        if opponent_move == "exit":
            print("Opponent exited the game.")
            break
        elif move == opponent_move:
            print(f"Both chose {move}. It's a tie!")
        elif (move == "rock" and opponent_move == "scissors") or \
             (move == "scissors" and opponent_move == "paper") or \
             (move == "paper" and opponent_move == "rock"):
            print(f"You chose {move}, opponent chose {opponent_move}. You win!")
        else:
            print(f"You chose {move}, opponent chose {opponent_move}. Opponent wins!")

def play_guess_the_number(conn):
    print("Starting Guess the Number game!")
    target_number = random.randint(1, 100)
    print("A target number between 1 and 100 has been chosen!")

    while True:
        try:
            player_guess = int(input("Enter your guess (1-100), or type -1 to exit: ").strip())
            if player_guess == -1:
                conn.send("exit".encode())
                print("Exiting game.")
                break
            elif not (1 <= player_guess <= 100):
                print("Invalid guess. Please enter a number between 1 and 100.")
                continue
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            continue

        conn.send(str(player_guess).encode())

        opponent_guess = conn.recv(1024).decode()
        if opponent_guess == "exit":
            print("Opponent exited the game.")
            break
        opponent_guess = int(opponent_guess)
        print(f"Opponent's guess: {opponent_guess}")

        player_diff = abs(target_number - player_guess)
        opponent_diff = abs(target_number - opponent_guess)

        if player_diff < opponent_diff:
            print(f"You win! The target number was {target_number}.")
        elif player_diff > opponent_diff:
            print(f"Opponent wins! The target number was {target_number}.")
        else:
            print(f"It's a tie! The target number was {target_number}.")

        play_again = input("Do you want to play again? (yes to continue, no to exit): ").strip().lower()
        if play_again != "yes":
            conn.send("exit".encode())
            print("Exiting game.")
            break
        else:
            conn.send("continue".encode())
            target_number = random.randint(1, 100)
            print("\nA new target number between 1 and 100 has been chosen!")

def logout(lobby_socket):
    message = {"action": "logout"}
    try:
        lobby_socket.send(json.dumps(message).encode())
        response_data = lobby_socket.recv(1024).decode()
        if response_data:
            response = json.loads(response_data)
            print(response.get("message", "Logout error"))
        else:
            print("No response from server during logout. Please try again.")
    except Exception as e:
        print(f"Error during logout: {e}")

if __name__ == "__main__":
    main()
