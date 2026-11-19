// DOM/transport contract tests using Node's standard library, no packages.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup(events) {
  const elements = {};
  function element() {
    const e = {children:[],style:{},value:'8',textContent:'',disabled:false,
      classList:{add(){}},setAttribute(name,value){this[name]=value;},appendChild(c){this.children.push(c);},prepend(c){this.children.unshift(c);}};
    Object.defineProperty(e,'innerHTML',{set(){e.children=[];}});
    Object.defineProperty(e,'lastChild',{get(){return {remove(){e.children.pop();}};}});
    return e;
  }
  for (const id of ['board','size','count','status','log','speed','start','step','play','next','reset']) elements[id]=element();
  const calls=[];
  const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:element},
    setTimeout: fn=>{fn();},
    fetch:async(url, options)=>{
      const request=JSON.parse(options.body); calls.push(request);
      let result;
      if(request.method==='queens.open') result={stream_id:'test',size:8};
      else if(request.method==='queens.close') result={closed:true};
      else {const event=events.shift() || {event:'done'};result={events:[event],done:event.event==='done'};}
      return {ok:true,json:async()=>({result})};
    }});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/client.js'),'utf8'),context);
  return {elements,calls,context};
}
async function settle(){for(let i=0;i<80;i++) await Promise.resolve();}

test('start opens without fetching; step requests exactly one and reset closes',async()=>{
  const {elements,calls}=setup([{event:'try',row:0,column:0,board:[]}]);
  elements.start.onclick();await settle();
  assert.deepEqual(calls.map(c=>c.method),['queens.open']);
  elements.step.onclick();await settle();
  assert.equal(calls[1].params.limit,1);
  assert.match(elements.status.textContent,/try/);
  assert.equal(elements.board.children.length,64);
  elements.reset.onclick();await settle();
  assert.equal(calls.at(-1).method,'queens.close');
  assert.equal(elements.count.textContent,0);
});

test('next solution stops before done; subsequent step completes',async()=>{
  const {elements,calls}=setup([{event:'place',row:0,column:0,board:[0]},
    {event:'solution',board:[0,4,7,5,2,6,1,3]},{event:'done'}]);
  elements.next.onclick();await settle();
  assert.equal(elements.count.textContent,1);
  assert.equal(elements.play.textContent,'Play');
  assert.equal(calls.filter(c=>c.method==='queens.next').length,2);
  elements.step.onclick();await settle();
  assert.match(elements.status.textContent,/Search complete/);
  const n=calls.length; elements.step.onclick();await settle(); assert.equal(calls.length,n);
});

test('network error is visible and controls recover',async()=>{
  const {elements,context}=setup([]);
  vm.runInContext("fetch=async()=>{throw new Error('offline');}",context);
  elements.start.onclick();await settle();
  assert.match(elements.status.textContent,/Error: offline/);
  assert.equal(elements.start.disabled,false);
});
