#!/usr/bin/env python3

import re

with open("tree.zig", "r") as f:
    data = f.read().split('\n')
first_real_line = 0
while not data[first_real_line].startswith("pub const node_list"):
    first_real_line += 1
first_real_line += 1
data = data[first_real_line:-2]

NODE_STRATEGY = 0
NODE_RED = 1
NODE_YELLOW = 2

def sanitize_steady_state(state_string):
    ret = ""
    for char in state_string:
        if char == '.':
            ret += 'f'
        elif char.isdigit():
            ret += char
    return ret

strategy = []
for line in data:
    if line.startswith("Node { .strategy"):
        pattern = "\".*\""
        search_data = re.search(pattern, line)
        strategy.append((NODE_STRATEGY, sanitize_steady_state(search_data.group())))
    elif line.startswith("Node { .red"):
        pattern = r"\D+(\d+)\D+(\d+).*(true|false)"
        search_data = re.search(pattern, line)
        strategy_data = search_data.groups()
        strategy.append((NODE_RED, int(strategy_data[0]), int(strategy_data[1]), strategy_data[2] == 'true'))
    elif line.startswith("Node { .yellow"):
        node_type = NODE_YELLOW
        transitions = []
        pattern = r"\.index = (\d+), .flip = (true|false)"
        for x in re.findall(pattern, line):
            transitions.append((int(x[0]), x[1] == 'true'))
        strategy.append((NODE_YELLOW, transitions))
    else:
        print("Unrecognized node type")
        break

def place_piece(column, value):
    for row in range(len(board)-1, -1, -1):
        if board[row][column] == 0:
            board[row][column] = value
            break
    else:
        print(f"Illegal move! ({column}, {value})")
        exit()

def display_board():
    for row in board:
        for col in row:
            if col == 0:
                print('. ',end='')
            else:
                print(f"{col} ",end='')
        print('|')

current_node = 1
board = []
for i in range(6):
    board.append([0] * 7)
flipped = False

while True:
    # red's move
    red_node = strategy[current_node]
    if red_node[0] == NODE_STRATEGY:
        for i in range(6):
            print(red_node[1][i*7:(i+1)*7])
        break
    elif red_node[0] != NODE_RED:
        print("Red strategy parity error")
        break
    red_column = red_node[1]
    if flipped:
        red_column = 6 - red_column
    current_node = red_node[2]
    flipped = flipped ^ red_node[3]
    place_piece(red_column, 1)

    display_board()

    yellow_column = int(input("Enter your move (1-7): "))-1

    yellow_node = strategy[current_node]
    if yellow_node[0] != NODE_YELLOW:
        print("Yellow strategy parity error")
        break
    flipped = flipped ^ yellow_node[1][yellow_column][1]
    current_node = yellow_node[1][yellow_column][0]
    place_piece(yellow_column, 2)
