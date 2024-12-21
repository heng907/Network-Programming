import socket
import time
import signal
import sys
from getpass import getpass 
import threading
import select
import os
import importlib.util
from ref.game_management import send_file_to_server, download_game

host_ips = {"linux1": "140.113.235.151",
            "linux2": "140.113.235.152",
            "linux3": "140.113.235.153",
            "linux4": "140.113.235.154",
            "heng": "127.0.0.1"}
ip_host = {"140.113.235.151": "linux1",
            "140.113.235.152": "linux2",
            "140.113.235.153": "linux3",
            "140.113.235.154": "linux4",
            "127.0.0.1": "heng"}

def signal_handler(sig, frame):

    sys.exit(0)  # Exit the program

def bold_green(text):
    return "\033[32;1m" + text + "\033[0m"

def bold_red(text):
    return "\033[31;1m" + text + "\033[0m"

def bold_blue(text):
    return "\033[34;1m" + text + "\033[0m"

def create_room(client):
    client.send("ready".encode())

    try:
        host = host_ips[socket.gethostname()]
        (port, game_type) = client.recv(1024).decode().strip().split(', ')
        port = int(port)
        game_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_server.bind((host, port))
        game_server.listen(1)
        client.send("room created successfully".encode())
    except socket.error as e:
        print("Error creating or binding server socket: \n")
        print("---------------------------------------")
        print(e)
        print("---------------------------------------\n")
        game_server = None
        client.send("error".encode())
        return
    try:
        while True and game_server != None:
            conn, addr = game_server.accept()
            print(bold_green(f"Player join from {ip_host[addr[0]]}! Game start!"))
            play_game(conn, game_type, player='server')
            print("Game over!")
            break
    except Exception as e:
        print(bold_red("Connection closed by the opponent. Back to lobby..."))
    conn.close()
    game_server.close()
    client.send("room close".encode())
    

def join_room(client):
    (host, port, game_type) = client.recv(1024).decode().strip().split(', ')
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, int(port)))
    try:
        print(bold_green("Connected to the server! Game start!"))
        play_game(conn,  game_type, player='client')
        print("Game over!")
    except Exception as e:
        print(bold_red("Connection closed by the opponent. Back to lobby..."))
    conn.close()
    client.send("room close".encode())
    

def play_game(conn, game_type, player):
    # 構建遊戲檔案的路徑
    game_file_path = f"{game_type}.py"
    
    # 檢查遊戲檔案是否存在
    if not os.path.isfile(game_file_path):
        print(f"Game file for '{game_type}' not found.")
        return
    
    # 動態導入遊戲模組
    spec = importlib.util.spec_from_file_location(game_type, game_file_path)
    game_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game_module)
    
    # 開始遊戲
    try:
        game_module.start_game(conn, player)
    except AttributeError:
        print(f"The game '{game_type}' does not have a 'start_game' function.")
    except Exception as e:
        print(f"Error during game execution: {e}")
        print("Returning to lobby...")

def listen_for_broadcast(client, listen_event):
    """
    Listen for broadcast messages from server while main thread handles user input
    """
    should_join_room = False
    while listen_event.is_set():
        try:
            # Only try to receive if there's data available
            client.setblocking(0)  # Set non-blocking
            try:
                message = client.recv(1024).decode()
                if message:
                    if "break input" in message:
                        print(("\nStatus updated. Please enter any key to continue."))
                        break
                    # if "join room" in message:
                    #     client.setblocking(1)
                    #     should_join_room = True
                    #     break
                    else:
                        # Print the message without interfering with any current input prompt
                        print("\n" + message)
                        print("\rEnter again: ", end='', flush=True)
            except socket.error:
                # No data available, continue
                time.sleep(0.1)
                continue
        except Exception as e:
            if listen_event.is_set():  # Only print error if we're not shutting down
                print(f"\nError receiving broadcast: {e}")
            break
    # if should_join_room:
    #     join_room(client, listen_event)

def receive_all_messages(client, timeout=0.1):
    """接收所有可用的消息並合併"""
    messages = []
    while True:
        ready = select.select([client], [], [], timeout)
        if not ready[0]:  # 如果沒有更多數據可讀
            break
        try:
            message = client.recv(1024).decode()
            if message:
                messages.append(message)
            else:  # 如果收到空消息，表示連接已關閉
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    return ''.join(messages)

def client_program():
    # Register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Create an event for stopping the broadcast thread
    listen_event = threading.Event()
    
    # Initialize broadcast_thread variable
    broadcast_thread = None

    # host = host_ips[socket.gethostname()]
    while True:
        try:
            host = input("Enter server IP: ").strip()
            port = int(input("Enter server port: "))
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            break
        except socket.error as e:
            print("Error creating or binding server socket: \n")
            print("---------------------------------------")
            print(e)
            print("---------------------------------------\n")
    
    time.sleep(0.1)
    try:
        while True:
            # Set blocking mode for main communication
            client.setblocking(1)
            server_message = receive_all_messages(client)
            if not server_message:
                continue
            
            if "Enter password:" in server_message:
                print("Enter password: ", end="", flush=True)
                password = getpass("")
                client.send(password.encode())
            elif "create room" in server_message:
                create_room(client)
            elif "join room" in server_message:
                join_room(client)
            elif "upload_game" in server_message:
                file_name = server_message.split(", ")[1]
                print(f"Uploading {file_name} to server...")
                send_file_to_server(client, file_name)
            elif "check_local_game" in server_message:
                file_name = server_message.split(", ")[1] + ".py"
                if os.path.isfile(file_name):
                    client.send("already_exist".encode())
                else:
                    client.send("not_exist".encode())
                    download_game(client, file_name)
            elif "Invitation sent. Waiting for acception..." in server_message:
                respond = client.recv(1024).decode()
                client.send(respond.encode())
            else:
                print(server_message, end="")
                if "Goodbye" in server_message:
                    break
                
                listen_event.set()
                # Start the broadcast listener thread before waiting for input
                if broadcast_thread is None or not broadcast_thread.is_alive():
                    broadcast_thread = threading.Thread(target=listen_for_broadcast, args=(client, listen_event))
                    broadcast_thread.daemon = True
                    broadcast_thread.start()
                if broadcast_thread and broadcast_thread.is_alive():
                    broadcast_thread.join(timeout=0.1)

                client_message = input()
                # Handle empty input
                if not client_message.strip():
                    # print("Input cannot be empty. Please try again: ", end="")
                    client_message = "invalid"
                
                # Stop the broadcast thread after input is received
                listen_event.clear()
                broadcast_thread = None
                
                client.send(client_message.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Signal the broadcast thread to stop
        listen_event.clear()
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    client_program()
