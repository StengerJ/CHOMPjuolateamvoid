#!/usr/bin/env python3
import socket, threading, json, sys

# Opcodes
OP_QUEUE   = 100
OP_LEAVE   = 101
OP_MATCHED = 110
OP_PEERLEFT= 111
OP_ERROR   = 120

ROWS, COLS = 4, 7

def print_board(board):
    for r in range(ROWS):
        line = ""
        for c in range(COLS):
            line += "X" if board[r][c] else "."
        print(line)
    print()

def apply_move(board, row, col):
    """Chomp off chocolate at (row,col) and all to top-right."""
    for r in range(row, ROWS):
        for c in range(col, COLS):
            board[r][c] = False

def valid_moves(board):
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]:
                moves.append((r, c))
    return moves


# --- Networking client ---
class PoisonedChocolateClient:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))
        self.file = self.sock.makefile("r", encoding="utf-8", newline="\n")
        self.room_id = None
        self.role = None
        self.board = [[True]*COLS for _ in range(ROWS)]

    def send(self, arr):
        msg = json.dumps(arr) + "\n"
        self.sock.sendall(msg.encode("utf-8"))

    def listen(self):
        while True:
            line = self.file.readline()
            if not line:
                print("Disconnected from server.")
                break
            try:
                msg = json.loads(line)
            except Exception:
                print("Bad message:", line)
                continue

            self.handle_message(msg)

    def handle_message(self, msg):
        if not isinstance(msg, list): return
        opcode = msg[0]

        if opcode == OP_MATCHED:
            self.room_id, self.role = msg[1], msg[2]
            print(f"Matched in room {self.room_id}, role {self.role}")
            print_board(self.board)
            if self.role == 0:
                self.make_move()

        elif opcode == OP_PEERLEFT:
            print("Peer disconnected.")
            self.sock.close()
            sys.exit(0)

        elif opcode == OP_ERROR:
            print("Server error:", msg)

        else:
            if isinstance(msg, list) and len(msg) == 2:
                r, c = msg
                print(f"Peer ate to ({r},{c})")
                apply_move(self.board, r, c)
                print_board(self.board)

                if (r, c) == (0, 0):
                    print(" You WIN! other player ate poison.")
                    self.sock.close()
                    sys.exit(0)
                else:
                    self.make_move()

    def make_move(self):
        moves = valid_moves(self.board)
        if not moves:
            print("No moves left. You lose.")
            self.sock.close()
            sys.exit(0)

        while True:
            try:
                user_input = input("Enter row col: ").strip()
                r, c = map(int, user_input.split())
            except Exception:
                print("Invalid input, use: row col")
                continue

            if (r, c) not in moves:
                print("Invalid move, try again.")
                continue

            break

        print(f"You moved at ({r},{c})")
        apply_move(self.board, r, c)
        print_board(self.board)
        self.send([r, c])

        if (r, c) == (0, 0):
            print(" You LOSE! Ate poison.")
            self.sock.close()
            sys.exit(0)


def main():
    host = input("enter host: ")
    port = int(input("enter port: "))
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} {host} {port}")
        sys.exit(2)

    client = PoisonedChocolateClient(host, port)

    client.send([OP_QUEUE])
    print("Queued")

    client.listen()


if __name__ == "__main__":
    main()
