import socket

def determine_winner(choice1, choice2):
    """
    判斷剪刀石頭布勝負:
    - "rock" > "scissors"
    - "scissors" > "paper"
    - "paper" > "rock"
    """
    if choice1 == choice2:
        return "draw"
    elif (choice1 == "rock" and choice2 == "scissors") or \
         (choice1 == "scissors" and choice2 == "paper") or \
         (choice1 == "paper" and choice2 == "rock"):
        return "player1"
    else:
        return "player2"

def start_game(conn, player):
    """
    雙人連線剪刀石頭布遊戲的邏輯。
    player: "server" 或 "client"
    conn:   與對方玩家的連接 (socket 物件)
    """
    # Ready handshake
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

    # Server 作為先出招的一方
    turn = (player == "server")

    valid_choices = ["rock", "paper", "scissors", "quit"]

    print("Welcome to Rock-Paper-Scissors!")
    print("Type 'rock', 'paper', or 'scissors' to play. Type 'quit' to exit.")

    while True:
        if turn:
            # 自己先出招
            while True:
                your_choice = input("Your move (rock/paper/scissors/quit): ").strip().lower()
                if your_choice in valid_choices:
                    break
                else:
                    print("Invalid choice, try again.")

            # 傳送自己的選擇給對方
            conn.send(your_choice.encode())
            if your_choice == "quit":
                print("You ended the game. Goodbye!")
                break

            # 接收對方的選擇
            opp_choice = conn.recv(1024).decode().strip()
            if opp_choice == "quit":
                print("Opponent ended the game. Goodbye!")
                break

            # 判斷勝負
            result = determine_winner(your_choice, opp_choice)
            print(f"Opponent chose: {opp_choice}")
            if result == "draw":
                print("It's a draw!")
            elif result == "player1":
                # player1 代表先出招的一方，也就是此時的自己
                if turn:
                    print("You win this round!")
                else:
                    print("You lose this round!")
            else:
                # result == "player2" 代表後出招的玩家獲勝，因為 turn == True 時自己是 player1
                if turn:
                    print("You lose this round!")
                else:
                    print("You win this round!")

        else:
            # 對方先出招
            print("\nWaiting for the opponent's move...")
            opp_choice = conn.recv(1024).decode().strip()
            if opp_choice == "quit":
                print("Opponent ended the game. Goodbye!")
                break

            # 輸入自己的選擇
            while True:
                your_choice = input("Your move (rock/paper/scissors/quit): ").strip().lower()
                if your_choice in valid_choices:
                    break
                else:
                    print("Invalid choice, try again.")

            conn.send(your_choice.encode())
            if your_choice == "quit":
                print("You ended the game. Goodbye!")
                break

            # 判斷勝負
            result = determine_winner(opp_choice, your_choice)
            print(f"Opponent chose: {opp_choice}")
            if result == "draw":
                print("It's a draw!")
            elif result == "player1":
                # player1 是先出招的一方，此時是對手
                if turn:
                    print("You lose this round!")
                else:
                    print("You win this round!")
            else:
                # player2 勝，此時 player2 是後出招(自己)
                if turn:
                    print("You win this round!")
                else:
                    print("You lose this round!")

        # 下回合對換先後手
        turn = not turn
