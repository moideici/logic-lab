"""Préférences légères ajoutées aux logits du réseau, sans accès caché."""
from .games import slide_2048, sudoku_candidates


def style_bias(obs, action, style):
    if style in ("balanced", "exploratory"):
        return 0.
    game, board = obs["game"], obs["board"]
    sign = 1 if style in ("positional", "defensive") else -.5
    if game in ("tictactoe", "connect4"):
        c = action.get("column", action.get("col"))
        return sign*.15*(1-abs(c-(len(board[0])-1)/2))
    if game == "2048":
        child, gain = slide_2048(board, action["direction"])
        empty = sum(v == 0 for row in child for v in row)
        return .1*empty if style in ("defensive", "positional") else .03*gain
    if game == "sudoku":
        if "undo" in action:
            return 0.
        n = len(sudoku_candidates(board, action["row"], action["col"]))
        return -.1*n if style in ("defensive", "positional") else .02*action["value"]
    if game == "minesweeper":
        r, c = action["row"], action["col"]
        known = sum(board[x][y] >= 0 for x in range(max(0, r-1), min(8, r+2)) for y in range(max(0, c-1), min(8, c+2)))
        return sign*.08*known
    if game == "sliding_puzzle":
        r,c=next((r,c) for r in range(3) for c in range(3) if not board[r][c])
        dr,dc={"up":(-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}[action["direction"]]
        value=board[r+dr][c+dc]
        tr,tc=divmod(value-1,3)
        improvement=abs(r+dr-tr)+abs(c+dc-tc)-abs(r-tr)-abs(c-tc)
        if style == "greedy":return .2*improvement
        if style == "positional":return .15*(r==tr and c==tc)
        if style == "defensive":return -.15*(r+dr==tr and c+dc==tc)
        return .1*improvement+.02*value
    return 0.
