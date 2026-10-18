import time
from logic_arena.labtrain import build_dataset
for g,tr,va,te in (('nim',3000,500,500),('tictactoe',3000,500,500),('connect4',300,80,80)):
    for split,n in (('train',tr),('val',va),('test',te)):
        t=time.time();d=build_dataset(g,split,n);print(g,split,n,d[0].shape,round(time.time()-t,1),'s',flush=True)
