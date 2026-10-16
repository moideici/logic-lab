"""Distances optimales des 181 440 états résolubles du taquin 3×3."""
import base64
from collections import deque
import json
from math import factorial
from pathlib import Path

FACT = [factorial(i) for i in range(10)]


def rank(board):
    return sum(sum(v < board[i] for v in board[i+1:])*FACT[8-i] for i in range(8))


def main():
    goal = (1,2,3,4,5,6,7,8,0)
    found = {goal:0}
    queue = deque([(goal,8)])
    while queue:
        board,zero = queue.popleft()
        r,c = divmod(zero,3)
        for offset,valid in ((-3,r>0),(3,r<2),(-1,c>0),(1,c<2)):
            if not valid:continue
            child=list(board);at=zero+offset
            child[zero],child[at]=child[at],0
            child=tuple(child)
            if child not in found:
                found[child]=found[board]+1
                queue.append((child,at))
    table=bytearray([255])*FACT[9]
    for board,distance in found.items():table[rank(board)]=distance
    assert len(found)==181440 and max(found.values())==31
    out=Path(__file__).resolve().parents[1]/'web'/'models'/'sliding-distances.json'
    out.write_text(json.dumps({'format':'logic-arena-exact-sliding-v1','goal':list(goal),'states':len(found),
        'diameter':31,'encoding':'base64-uint8-lehmer-9','data':base64.b64encode(table).decode()},separators=(',',':')))
    print(f'{len(found)} états · distance maximale 31 · {out}')


if __name__=='__main__':main()
