import sys
import os
import argparse

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chess
from engine.engine import Agent

def uci_loop():
    # Setup CLI arguments so you can configure different versions in tournaments
    parser = argparse.ArgumentParser(description="bolt UCI wrapper")
    parser.add_argument("--method", choices=["minimax", "minimax_ab", "minimax_ab_qs", "negamax_tt", "random"], default="minimax_ab", help="The search method to use")
    parser.add_argument("--depth", type=int, default=3, help="Default search depth for minimax")
    parser.add_argument("--no-info", action="store_true", help="Disable outputting standard UCI info logs")
    args, unknown = parser.parse_known_args()
    
    board = chess.Board()
    agent = Agent(method=args.method)
    default_depth = args.depth
    
    # Customize name depending on method so we can see which is which in tournament standings
    engine_name = f"bolt_{args.method}"
    if args.method == "minimax":
        engine_name += f"_d{default_depth}"
    
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        line = line.strip()
        if not line:
            continue
            
        parts = line.split()
        command = parts[0]
        
        if command == "uci":
            print(f"id name {engine_name}")
            print("id author ragnar")
            print("uciok")
            sys.stdout.flush()
            
        elif command == "isready":
            print("readyok")
            sys.stdout.flush()
            
        elif command == "ucinewgame":
            board = chess.Board()
            
        elif command == "position":
            if len(parts) >= 2:
                if parts[1] == "startpos":
                    board = chess.Board()
                elif parts[1] == "fen":
                    if "moves" in parts:
                        moves_idx = parts.index("moves")
                        fen_str = " ".join(parts[2:moves_idx])
                    else:
                        fen_str = " ".join(parts[2:])
                    board = chess.Board(fen_str)
                else:
                    continue
                
                # Push any trailing moves
                if "moves" in parts:
                    moves_idx = parts.index("moves")
                    for move_str in parts[moves_idx + 1:]:
                        try:
                            board.push_uci(move_str)
                        except ValueError:
                            pass
                            
        elif command == "go":
            depth = default_depth
            if "depth" in parts:
                try:
                    depth_idx = parts.index("depth")
                    depth = int(parts[depth_idx + 1])
                except (ValueError, IndexError):
                    pass
            
            # Find the best move for the current position
            move = agent.find_move(board, depth=depth)
            if move:
                if not args.no_info:
                    # Compute evaluation score from the current player's perspective to report in 'info'
                    board.push(move)
                    score = agent.evaluate(board)
                    board.pop()
                    
                    relative_score = score if board.turn == chess.WHITE else -score
                    
                    print(f"info depth {depth} score cp {relative_score} nodes {agent.nodes_searched}")
                    sys.stdout.flush()
                
                print(f"bestmove {move.uci()}")
            else:
                print("bestmove 0000")
            sys.stdout.flush()
            
        elif command == "quit":
            break

if __name__ == "__main__":
    uci_loop()