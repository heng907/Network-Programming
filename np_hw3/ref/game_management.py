from ref.msg_management import *
import threading
import os
import time
lock = threading.Lock()
user_games = {}

def game_management_interface(conn, user):
    while True:
        conn.send("\nGame Management:\n[1] List your games\n[2] Upload a new game\n[3] Back to lobby\nEnter: ".encode())
        option = conn.recv(1024).decode().strip()
        
        if option == "1":
            list_user_games(conn, user)
        elif option == "2":
            upload_game(conn, user)
        elif option == "3":
            break
        else:
            invalid(conn)

def list_user_games(conn, user):
    if user not in user_games or not user_games[user]:
        failed_msg(conn, "There is no games.")
        return

    game_list = "\033[1;43mYour Games:\033[0m\n"
    for idx, game in enumerate(user_games[user], start=1):
        game_list += (f"{idx}. Game Name: {game['game_name']}, "
                      f"Description: {game['description']}\n")
    
    list_msg(conn, game_list)
    
def upload_game(conn, user):
    conn.send("Enter game name: ".encode())
    game_name = conn.recv(1024).decode().strip()
    
    conn.send("Enter game description: ".encode())
    description = conn.recv(1024).decode().strip()
    
    # conn.send(bold_blue("Please place the game file in the same directory as the server.\nAnd make sure the file name is clear and correct.\n").encode())
    conn.send("Enter file name to upload: ".encode())
    file_name = conn.recv(1024).decode().strip()

    # Simulate file upload
    try:
        server_file_path = f"game_files/{game_name}.py"
        receive_file_from_client(conn, game_name, file_name)
        with lock:
            # Update user_games data structure
            if user not in user_games:
                user_games[user] = []

            user_games[user].append({
                "game_name": game_name,
                "description": description,
                "file_path": server_file_path,
                "developer": user
            })
        
    except Exception as e:
        failed_msg(conn, f"Error uploading game: {e}")

def download_game(client_socket, file_name):
    file_size = int(client_socket.recv(1024).decode())
    
    client_socket.send("ACK".encode())
    
    received_data = b''
    while len(received_data) < file_size:
        packet = client_socket.recv(4096)
        if not packet:
            break
        received_data += packet

    
    with open(file_name, 'wb') as f:
        f.write(received_data)
    
    client_socket.send("ACK".encode())

def send_game_to_client(conn, user, game_name):
    server_file_path = f"game_files/{game_name}.py"
    
    conn.send(f"check_local_game, {game_name}".encode())
    msg = conn.recv(1024).decode()
    if msg == "already_exist":
        system_msg(conn, f"Game '{game_name}' already exists locally.")
        return


    try:
        
        with open(server_file_path, 'rb') as f:
            file_data = f.read()
        file_size = len(file_data)
        conn.send(f"{file_size}".encode())
        ack = conn.recv(1024).decode()
        if ack != "ACK":
            failed_msg(conn, "Failed to receive acknowledgment from server.")
            return
        conn.sendall(file_data)

        conn.recv(1024).decode()
        success_msg(conn, f"Game '{game_name}' downloaded successfully.")
        
    except Exception as e:
        conn.send(f"error downloading game: {e}".encode())



def receive_file_from_client(conn, game_name, file_name):
    server_file_path = f"game_files/{game_name}.py"
    try:
        conn.send(f"upload_game, {file_name}.py".encode())
        msg = conn.recv(1024).decode()
        if msg == "not_found":
            failed_msg(conn, "File not found. Please check the file name and try again.")
            return
        file_size = int(msg)
        
        conn.sendall("ACK".encode())
        
        received_data = b''
        while len(received_data) < file_size:
            packet = conn.recv(4096)
            if not packet:
                break
            received_data += packet
        
        directory = os.path.dirname(server_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(server_file_path, 'wb') as f:
            f.write(received_data)
        
        success_msg(conn, "\033[1;42mGame uploaded successfully.\033[0m")

    except Exception as e:
        failed_msg(conn, f"Error receiving file: {e}")

def send_file_to_server(client_socket, file_path):
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        file_size = len(file_data)
        client_socket.sendall(f"{file_size}".encode())
    
        ack = client_socket.recv(1024).decode()
        if ack != "ACK":
            print("Failed to receive acknowledgment from server.")
            return
    
        client_socket.sendall(file_data)
    except FileNotFoundError:
        client_socket.send("not_found".encode())
    except Exception as e:
        print(f"Error sending file: {e}")

def get_all_games():
    return user_games

def list_games(conn):
    room_list = "\nGames:\n"
    if user_games:
        check = False
        for room_name, details in user_games.items():
            if details['public']:
                room_list += (f"- Room Name: {room_name}"
                              f"\n  (1) Game Type: {details['type']}"
                              f"\n  (2) Status: {details['status']}"
                              f"\n  (3) Host: {details['owner']}\n")
                check = True
        if not check:
            room_list += "No rooms available.\n"
        return True
    else:
        room_list += "No games available.\n"
        return False
    
    return room_list

def list_all_games(conn):
    game_list = "All Games:\n\n"
    if user_games:
        candidates = []
        for username, games in user_games.items():
            for idx, game in enumerate(games, start=1):
                game_list += (f"   {idx}. Game Name: {game['game_name']}\n"
                              f"    (1) Description: {game['description']}\n"
                              f"    (2) Developer: {game['developer']}\n")
                candidates.append(game['game_name'])
        list_msg(conn, game_list)
        return candidates
    else:
        game_list += "No games available.\n"
        list_msg(conn, game_list)
        return None