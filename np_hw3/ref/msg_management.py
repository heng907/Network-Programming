import threading

welcome = """\033[1;34;45m
  _    _  _    _     _____  _  _               _   
 | |  | |(_)  | |   / ____|| |(_)             | |  
 | |__| | _   | |  | |     | | _   ___  _ __  | |_ 
 |  __  || |  | |  | |     | || | / _ \| '_ \ | __|
 | |  | || |  |_|  | |____ | || ||  __/| | | || |_ 
 |_|  |_||_|  (_)   \_____||_||_| \___||_| |_| \__|
                                                   \033[0m\n"""


def welcome_msg(conn):
    conn.send(welcome.encode())

def invalid(conn):
    failed_msg(conn, "Invalid option. Try again.")

def bold_green(text):
    return "\033[32;1m" + text + "\033[0m"

def bold_red(text):
    return "\033[31;1m" + text + "\033[0m"

def bold_blue(text):
    return "\033[36;1m" + text + "\033[0m"

def list_msg(conn, text):
    conn.send((bold_blue(text)).encode())

def success_msg(conn, text):
    conn.send((bold_green(text)).encode())

def failed_msg(conn, text):
    conn.send((bold_red(text)).encode())

def system_msg(conn, text):
    conn.send(bold_blue("~BROADCASTING~ " + text).encode())

def broadcast_message(message, exclude_conn):
    from ref.registers_management import online_lock, online_players

    def send_to_client(conn, message):
        try:
            system_msg(conn, message)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")

    all_conn = []
    with online_lock:
        for conn, _, _ in online_players.values():
            all_conn.append(conn)
    
    for conn in all_conn:
        if conn != exclude_conn:
            threading.Thread(target=send_to_client, 
                            args=(conn, message), 
                            daemon=True).start()
