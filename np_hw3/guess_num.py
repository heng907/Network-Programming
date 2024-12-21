import socket
import random

def start_game(conn, player):
    """
    雙人連線猜數字遊戲的主要邏輯。
    player: "server" 或 "client"
    conn: 與對方玩家的連接 (socket 物件)
    """
    # 選擇自己的秘密數字
    secret_number = random.randint(1, 100)
    print(f"Your secret number is: {secret_number}")

    # 通知對方自己準備好 (透過簡單的 "ready" 訊息)
    if player == "server":
        # Server 先傳送 "ready" 給 Client
        conn.send("ready".encode())
        # 等待 Client 傳回 "ready"
        opp_ready = conn.recv(1024).decode().strip()
        if opp_ready != "ready":
            print("Opponent did not respond with 'ready'. Exiting.")
            return
    else:
        # Client 等待 Server 傳送 "ready"
        server_ready = conn.recv(1024).decode().strip()
        if server_ready != "ready":
            print("Server did not send 'ready'. Exiting.")
            return
        # Client 傳回 "ready"
        conn.send("ready".encode())

    # 遊戲開始，server 為先猜的一方
    # 若 player == "server"，turn = True 表示由自己先猜
    # 若 player == "client"，turn = False 表示由對方（server）先猜
    turn = (player == "server")

    while True:
        if turn:
            # 輸入自己的猜測
            while True:
                try:
                    guess = int(input("Enter your guess (1-100): "))
                    if 1 <= guess <= 100:
                        break
                    else:
                        print("Please enter a number between 1 and 100.")
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
            
            # 將猜測傳給對方
            conn.send(str(guess).encode())

            # 接收對方的回應
            response = conn.recv(1024).decode().strip()
            if response == "correct":
                print("You guessed the opponent's secret number! You win!")
                break
            elif response == "too high":
                print("Your guess is too high. Try again next turn.")
            elif response == "too low":
                print("Your guess is too low. Try again next turn.")
            else:
                print("Unexpected response from opponent.")
                break

        else:
            # 等待對方的猜測數字
            print("\nWaiting for the opponent's guess...")
            data = conn.recv(1024)
            if not data:
                print("Connection lost with the opponent.")
                break

            opponent_guess = data.decode().strip()
            if not opponent_guess.isdigit():
                print("Invalid guess received from opponent.")
                break
            opponent_guess = int(opponent_guess)

            # 比對猜測結果
            if opponent_guess == secret_number:
                # 對方猜中你的數字
                conn.send("correct".encode())
                print("Opponent guessed your number. You lose!")
                break
            elif opponent_guess > secret_number:
                conn.send("too high".encode())
            else:
                conn.send("too low".encode())

        # 換下一回合
        turn = not turn
