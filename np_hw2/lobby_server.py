import socket
import threading
import json

# Used to store registered users
# {'username': {'password': 'pwd', 'status': 'idle', 'conn': conn}}
registered_users = {}

# Used to store rooms
# {'room_id': {'creator': 'username', 'game_type': 'type', 'status': 'waiting', 'type': 'public/private', 'invited_players': [], 'ip': 'creator_ip', 'tcp_port': port}}
rooms = {}

lock = threading.Lock()

def handle_client(conn, addr):
    current_user = None
    try:
        while True:
            message = conn.recv(4096).decode()
            if message:
                request = json.loads(message)
                action = request.get("action")

                if action == "register":
                    username = request.get("username")
                    password = request.get("password")
                    with lock:
                        if username in registered_users:
                            response = {"status": "error", "message": "Username already exists."}
                        else:
                            registered_users[username] = {"password": password, "status": "offline", "conn": None}
                            response = {"status": "success", "message": "Registration successful."}
                    conn.send(json.dumps(response).encode())

                elif action == "login":
                    username = request.get("username")
                    with lock:
                        if username not in registered_users:
                            response = {"status": "error", "message": "User does not exist."}
                            conn.send(json.dumps(response).encode())
                        else:
                            conn.send(json.dumps({"status": "prompt", "message": "Enter password:"}).encode())
                            password = conn.recv(4096).decode()
                            if password == registered_users[username]["password"]:
                                registered_users[username]["status"] = "idle"
                                registered_users[username]["conn"] = conn
                                current_user = username
                                response = {
                                    "status": "success",
                                    "message": "Login successful.",
                                    "online_players": {user: data["status"] for user, data in registered_users.items()},
                                    "rooms": {room_id: room_info for room_id, room_info in rooms.items() if room_info["type"] == "public" and room_info["status"] == "waiting"}
                                }
                            else:
                                response = {"status": "error", "message": "Incorrect password."}
                            conn.send(json.dumps(response).encode())

                elif action == "create_room" and current_user:
                    room_id = request.get("room_id")
                    game_type = request.get("game_type")
                    room_type = request.get("room_type", "public")
                    tcp_port = request.get("tcp_port")
                    with lock:
                        if room_id in rooms:
                            response = {"status": "error", "message": "Room ID already exists. Choose a different ID."}
                        else:
                            rooms[room_id] = {
                                "creator": current_user,
                                "game_type": game_type,
                                "status": "waiting",
                                "type": room_type,
                                "players": [current_user],
                                "invited_players": [],
                                "ip": addr[0],
                                "tcp_port": tcp_port
                            }
                            registered_users[current_user]["status"] = "in_room"
                            response = {"status": "success", "message": f"Room '{room_id}' created successfully.", "room_id": room_id}
                    conn.send(json.dumps(response).encode())

                elif action == "invite_player" and current_user:
                    to_user = request.get("to_user")
                    room_id = request.get("room_id")
                    with lock:
                        if to_user not in registered_users:
                            response = {"status": "error", "message": f"User {to_user} does not exist."}
                        elif registered_users[to_user]["status"] != "idle":
                            response = {"status": "error", "message": f"User {to_user} is not idle."}
                        else:
                            invite_message = {
                                "action": "invite",
                                "from_user": current_user,
                                "room_id": room_id,
                                "game_type": rooms[room_id]["game_type"]
                            }
                            to_conn = registered_users[to_user]["conn"]
                            to_conn.send(json.dumps(invite_message).encode())
                            response = {"status": "success", "message": f"Invitation sent to {to_user}."}
                    conn.send(json.dumps(response).encode())

                elif action == "respond_invite" and current_user:
                    from_user = request.get("from_user")
                    room_id = request.get("room_id")
                    invite_response = request.get("response")
                    with lock:
                        if from_user in registered_users:
                            from_conn = registered_users[from_user]["conn"]
                            if invite_response == "yes":
                                rooms[room_id]["players"].append(current_user)
                                registered_users[current_user]["status"] = "in_game"
                                rooms[room_id]["status"] = "in_game"
                                response = {"status": "success", "message": f"{current_user} accepted your invitation."}
                                from_conn.send(json.dumps(response).encode())
                            else:
                                response = {"status": "declined", "message": f"{current_user} declined your invitation."}
                                from_conn.send(json.dumps(response).encode())
                        else:
                            response = {"status": "error", "message": f"User {from_user} not found."}
                    # No need to send response to the invited user
                    # Since they proceed to join the room if they accepted

                elif action == "get_idle_players" and current_user:
                    with lock:
                        idle_players = [user for user, data in registered_users.items() if data["status"] == "idle" and user != current_user]
                    response = {"status": "success", "idle_players": idle_players}
                    conn.send(json.dumps(response).encode())

                elif action == "join_room" and current_user:
                    room_id = request.get("room_id")
                    with lock:
                        if room_id in rooms:
                            room_info = rooms[room_id]
                            if room_info["type"] == "public" and room_info["status"] == "waiting":
                                room_info["players"].append(current_user)
                                room_info["status"] = "in_game"
                                registered_users[current_user]["status"] = "in_game"
                                response = {
                                    "status": "success",
                                    "message": f"Joined public room {room_id}.",
                                    "game_ip": room_info["ip"],
                                    "game_port": room_info["tcp_port"],
                                    "game_type": room_info["game_type"]
                                }
                            elif room_info["type"] == "private":
                                if current_user in room_info["players"]:
                                    registered_users[current_user]["status"] = "in_game"
                                    room_info["status"] = "in_game"
                                    response = {
                                        "status": "success",
                                        "message": f"Joined private room {room_id}.",
                                        "game_ip": room_info["ip"],
                                        "game_port": room_info["tcp_port"],
                                        "game_type": room_info["game_type"]
                                    }
                                else:
                                    response = {"status": "error", "message": "Cannot join private room without invitation."}
                            else:
                                response = {"status": "error", "message": "Room not available or in-game."}
                        else:
                            response = {"status": "error", "message": "Room does not exist."}
                    conn.send(json.dumps(response).encode())

                elif action == "game_over" and current_user:
                    room_id = request.get("room_id")
                    with lock:
                        if room_id and room_id in rooms and rooms[room_id]["creator"] == current_user:
                            # Remove the room
                            del rooms[room_id]
                            registered_users[current_user]["status"] = "idle"
                            response = {"status": "success", "message": "Game over, room removed."}
                        else:
                            registered_users[current_user]["status"] = "idle"
                            response = {"status": "success", "message": "Game over, status updated."}
                    conn.send(json.dumps(response).encode())

                elif action == "logout" and current_user:
                    with lock:
                        registered_users[current_user]["status"] = "offline"
                        registered_users[current_user]["conn"] = None
                    response = {"status": "success", "message": "Logout successful."}
                    conn.send(json.dumps(response).encode())
                    break

                else:
                    response = {"status": "error", "message": "Unknown command or not logged in."}
                    conn.send(json.dumps(response).encode())
            else:
                break
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        if current_user:
            with lock:
                registered_users[current_user]["status"] = "offline"
                registered_users[current_user]["conn"] = None
        conn.close()
        print(f"Player from {addr} has disconnected.")

def start_lobby_server(ip, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ip, port))
        server_socket.listen(5)
        print(f"Lobby server started on IP {ip} and port {port}. Waiting for player connections...")

        while True:
            conn, addr = server_socket.accept()
            print(f"Player connected from {addr}")
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except OSError as e:
        print(f"Failed to start lobby server on IP {ip} and port {port}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred on IP {ip} and port {port}: {e}")

if __name__ == "__main__":
    ip = '140.113.235.151'  # Bind to all interfaces
    port = 16001
    start_lobby_server(ip, port)
