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

def clone_board(board):
    r = []
    for x in board:
        r.append(x.copy())
    return r

def place_piece(board, column, value):
    for row in range(len(board)-1, -1, -1):
        if board[row][column] == 0:
            board[row][column] = value
            break
    else:
        print(f"Illegal move! ({column}, {value})")
        exit()

def new_board():
    ret = []
    for i in range(6):
        ret.append([0] * 7)
    return ret

def flip_board(board):
    for i in range(len(board)):
        board[i] = board[i][::-1]

def flip_string(string):
    ret = ""
    for x in string:
        ret += str(8 - int(x))
    return ret

def overlay_steady_state(board, strategy):
    ret = []
    for i in range(len(board)):
        this_row = ""
        for j in range(len(board[i])):
            if board[i][j] == 1:
                this_row += "R"
                continue
            elif board[i][j] == 2:
                this_row += "Y"
                continue
            this_row += strategy[i*7+j]
        ret.append(this_row)
    return ret

def clean_state(state):
    ret = ""
    for x in state:
        if x == "R" or x == "Y":
            ret += x
        else:
            ret += "."
    return ret

def red_wins(board):
    for i in range(6):
        for j in range(7-3):
            if board[i][j] == board[i][j+1] == board[i][j+2] == board[i][j+3] == 1:
                return True
    for i in range(6-3):
        for j in range(7):
            if board[i][j] == board[i+1][j] == board[i+2][j] == board[i+3][j] == 1:
                return True
    for i in range(6-3):
        for j in range(7-3):
            if board[i][j] == board[i+1][j+1] == board[i+2][j+2] == board[i+3][j+3] == 1:
                return True
    for i in range(3, 6):
        for j in range(7-3):
            if board[i][j] == board[i-1][j+1] == board[i-2][j+2] == board[i-3][j+3] == 1:
                return True
    return False

def has_win(board):
    for i in range(7):
        if board[0][i] != 0:
            continue
        with_move = clone_board(board)
        place_piece(with_move, i, 1)
        if red_wins(with_move):
            return True
    return False

# node id => [(board position, representative string)]
representatives = {}

# (node id, board state, representative string)
unexplored = []
unexplored.append((1, new_board(), ""))

while len(unexplored) != 0:
    red_node = unexplored.pop()
    if not red_node[0] in representatives:
        representatives[red_node[0]] = []

    if has_win(red_node[1]):
        continue

    # we've seen this exact position on the same node id, we've just taken two
    # different paths to get there
    is_transposition = False
    for prev_seen in representatives[red_node[0]]:
        if prev_seen[0] == red_node[1]:
            is_transposition = True
            break
    if is_transposition:
        continue

    representatives[red_node[0]].append((red_node[1], red_node[2]))

    # we've reached a steady state
    if strategy[red_node[0]][0] == NODE_STRATEGY:
        continue
    elif strategy[red_node[0]][0] != NODE_RED:
        print("parity issue with red move")
        break

    new_board = clone_board(red_node[1])
    red_column = strategy[red_node[0]][1]
    new_state = strategy[red_node[0]][2]
    place_piece(new_board, red_column, 1)
    state_string = red_node[2] + str(red_column+1)
    should_flip = strategy[red_node[0]][3]
    if should_flip:
        flip_board(new_board)
        state_string = flip_string(state_string)

    for yellow_column in range(7):
        # this is an illegal move
        if new_board[0][yellow_column] != 0:
            continue

        yellow_strategy = strategy[new_state]
        yellow_board = clone_board(new_board)
        place_piece(yellow_board, yellow_column, 2)
        yellow_state_string = state_string + str(yellow_column + 1)

        transition = yellow_strategy[1][yellow_column]
        if transition[1]:
            flip_board(yellow_board)
            yellow_state_string = flip_string(yellow_state_string)
        unexplored.append((transition[0], yellow_board, yellow_state_string))

branches_json = {}
steady_states_json = []
seen_states = set()
for x in representatives:
    if strategy[x][0] == NODE_RED:
        red_column = strategy[x][1]
        for position in representatives[x]:
            branches_json[position[1]] = str(red_column+1)
    elif strategy[x][0] == NODE_STRATEGY:
        for position in representatives[x]:
            steady_state = overlay_steady_state(position[0], strategy[x][1])
            state_string_1 = clean_state("".join(steady_state))
            state_string_2 = clean_state("".join([row[::-1] for row in steady_state]))
            if state_string_1 in seen_states or state_string_2 in seen_states:
                continue
            seen_states.add(state_string_2)
            steady_states_json.append(steady_state)

with open("branches.json", "w") as branches_file:
    print("{", file=branches_file)
    print_comma = False
    for k in branches_json:
        if print_comma:
            print(",", file=branches_file)
        print_comma = True

        print(f"  \"{k}\": \"{branches_json[k]}\"", end='', file=branches_file)
    print("\n}", file=branches_file)

with open("steady_states.json", "w") as steady_states_file:
    print("[", file=steady_states_file)
    for i in range(len(steady_states_json)):
        if i == 0:
            print("  [", file=steady_states_file)
        else:
            print("  ], [", file=steady_states_file)

        for j in range(len(steady_states_json[i])):
            end = "\n" if j == len(steady_states_json[i])-1 else ",\n"
            print(f"    \"{steady_states_json[i][j]}\"", file=steady_states_file, end=end)
    print("  ]", file=steady_states_file)
    print("]", file=steady_states_file)

print(len(branches_json))
print(len(steady_states_json))
