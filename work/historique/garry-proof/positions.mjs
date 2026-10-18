import fs from 'node:fs';
const root='C:/Users/gabor/code/playi',dir='C:/Users/gabor/code/logic-lab/work/garry-proof';
const {Game,GarryModel,rng}=await import(`file:///${root}/web/engine.js`);
const load=async p=>(await WebAssembly.instantiate(fs.readFileSync(p),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const before=await load(`${dir}/before.wasm`),after=await load(`${dir}/candidate.wasm`),oracle=await load(`${dir}/candidate.wasm`),model=new GarryModel(JSON.parse(fs.readFileSync(`${dir}/before.json`)));
for(const rt of [before,after]){rt.enableValue(1);model.positionHead.weights.forEach((w,i)=>rt.setValueWeight(i,w));}
const [seedText='17033500',countText='128',output=`${dir}/positions.json`]=process.argv.slice(2);
const report={seed:Number(seedText),requested:Number(countText),nodes:200000,oracle_limit:100000000,oracle_time_ms:5000,samples:[],before:{optimal:0,errors:0,unresolved:0,losing_blunders:0},after:{optimal:0,errors:0,unresolved:0,losing_blunders:0},paired_known:0,paired_before_errors:0,paired_after_errors:0};
function bits(o){const b=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)b[p]|=1n<<BigInt(c*7+5-r)}));return b;}
function won(o,p){const b=o.board;for(let r=0;r<6;r++)for(let c=0;c<7;c++)for(const [dr,dc]of[[0,1],[1,0],[1,1],[1,-1]]){let n=0;for(let k=0;k<4;k++){const y=r+k*dr,x=c+k*dc;if(y<6&&x>=0&&x<7&&b[y][x]===p)n++;}if(n===4)return true;}return false;}
function next(o,c){const board=o.board.map(r=>r.slice()),r=board.map(row=>row[c]).lastIndexOf(0);board[r][c]=o.current_player;return {...o,board,current_player:3-o.current_player,moves:o.moves+1};}
function solve(o){if(won(o,3-o.current_player))return -1;const b=bits(o);oracle.certify(b[1],b[2],o.current_player,report.oracle_limit,report.oracle_time_ms);return ({2:1,3:0,4:-1})[oracle.getProofState()]??null;}
for(let episode=0;report.samples.length<report.requested;episode++){
 const seed=report.seed+episode,random=rng(seed),g=new Game('connect4',seed),history=[];
 for(let i=0;i<12+episode%15;i++){
  const options=g.legal().filter(a=>!won(next(g.obs(),a.column),g.player));if(!options.length)break;
  const a=options[Math.floor(random()*options.length)];g.step(a);history.push(a.column);
 }
 const o=g.obs();if(g.done||g.moves<12||g.legal().length<2||g.legal().some(a=>won(next(o,a.column),g.player)))continue;
 const expected=solve(o),sample={seed,history,observation:o,expected,before:null,after:null};
 for(const [name,rt,method]of[['before',before,'decide'],['after',after,'decideVerified']]){
  const b=bits(o),z=model.forGame('connect4').forward(o).z;[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>rt.setPrior(c,7-i));
  const c=rt[method](b[1],b[2],o.current_player,report.nodes,2000,42),value=solve(next(o,c)),actual=value===null?null:-value;
  sample[name]={column:c,outcome:actual,depth:rt.getDepth(),nodes:rt.getNodes(),certificate:name==='after'?rt.getProofState():0};
  report[name][expected===null||actual===null?'unresolved':actual===expected?'optimal':'errors']++;
  if(expected!==null&&expected>=0&&actual!==null&&actual<0)report[name].losing_blunders++;
 }
 if(expected!==null&&sample.before.outcome!==null&&sample.after.outcome!==null){report.paired_known++;if(sample.before.outcome!==expected)report.paired_before_errors++;if(sample.after.outcome!==expected)report.paired_after_errors++;}
 report.samples.push(sample);
 if(report.samples.length%8===0){fs.writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify({completed:report.samples.length,before:report.before,after:report.after,paired_before_errors:report.paired_before_errors,paired_after_errors:report.paired_after_errors}));}
}
report.completed=true;fs.writeFileSync(output,JSON.stringify(report,null,2));
