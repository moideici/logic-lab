"""Public-board bit-mask solver; environment answers never enter observations."""
def solve_sudoku(board,limit=2,tick=lambda:None):
 b=[r[:] for r in board];rows=[0]*9;cols=[0]*9;boxes=[0]*9;solutions=[]
 for r in range(9):
  for c in range(9):
   v=b[r][c]
   if not v:continue
   bit=1<<v;k=3*(r//3)+c//3
   if (rows[r]|cols[c]|boxes[k])&bit:return solutions,True
   rows[r]|=bit;cols[c]|=bit;boxes[k]|=bit
 def visit():
  tick();cell=None
  for r in range(9):
   for c in range(9):
    if b[r][c]:continue
    k=3*(r//3)+c//3;mask=1022&~(rows[r]|cols[c]|boxes[k]);count=mask.bit_count()
    if not mask:return
    if cell is None or count<cell[0]:cell=(count,r,c,k,mask)
  if cell is None:solutions.append([r[:] for r in b]);return
  _,r,c,k,mask=cell
  while mask:
   bit=mask&-mask;mask-=bit;b[r][c]=bit.bit_length()-1;rows[r]|=bit;cols[c]|=bit;boxes[k]|=bit
   try:visit()
   finally:b[r][c]=0;rows[r]^=bit;cols[c]^=bit;boxes[k]^=bit
   if len(solutions)>=limit:return
 from .agents import Exhausted
 try:visit()
 except Exhausted:return solutions,False
 return solutions,True
