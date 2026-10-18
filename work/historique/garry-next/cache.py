from pathlib import Path
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'cached';s=(ROOT/'search/connect4-search.ts').read_text(encoding='utf-8')
s=s.replace('function evaluate(position:u64,mask:u64):i32{', '''const EVAL_SIZE:i32=1<<18;
const evalKeys=new StaticArray<u64>(EVAL_SIZE);
const evalValues=new StaticArray<i32>(EVAL_SIZE);
const evalTags=new StaticArray<u32>(EVAL_SIZE);
let evalEpoch:u32=1;
function invalidateEval():void{evalEpoch++;if(!evalEpoch){memory.fill(changetype<usize>(evalTags),0,EVAL_SIZE*4);evalEpoch=1;}}
function evaluate(position:u64,mask:u64):i32{
 const key=position+mask,index=<i32>((key*<u64>0x9e3779b97f4a7c15)>>46);
 if(evalTags[index]==evalEpoch&&evalKeys[index]==key)return evalValues[index];
 const score=rawEvaluate(position,mask);evalKeys[index]=key;evalValues[index]=score;evalTags[index]=evalEpoch;return score;
}
function rawEvaluate(position:u64,mask:u64):i32{''')
s=s.replace('initialize();nodes=0;', 'initialize();invalidateEval();nodes=0;')
s=s.replace('if(index>=0&&index<32)valueWeights[index]=value;', 'if(index>=0&&index<32){valueWeights[index]=value;invalidateEval();}')
s=s.replace('learned=enabled!=0;', 'learned=enabled!=0;invalidateEval();')
f=OUT/'search/connect4-search.ts';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8',newline='\n')
