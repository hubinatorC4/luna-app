// Zbiera napisy EN z plików JS: wartości pod kluczem "en" (string/array/object/template).
const fs=require('fs'),path=require('path'),acorn=require('acorn'),walk=require('acorn-walk');
const dir=process.argv[2]; const out={};
function leaves(n,acc,file){
  if(!n) return;
  if(n.type==='Literal'&&typeof n.value==='string'){acc.push({s:n.value,file});return;}
  if(n.type==='TemplateLiteral'){acc.push({s:n.quasis.map((q,i)=>q.value.cooked+(i<n.expressions.length?'{'+i+'}':'')).join(''),file,tpl:n.expressions.length>0});return;}
  if(n.type==='ArrayExpression'){n.elements.forEach(e=>leaves(e,acc,file));return;}
  if(n.type==='ObjectExpression'){n.properties.forEach(p=>p.value&&leaves(p.value,acc,file));return;}
  if(n.type==='BinaryExpression'&&n.operator==='+'){leaves(n.left,acc,file);leaves(n.right,acc,file);return;}
  if(n.type==='ConditionalExpression'){leaves(n.consequent,acc,file);leaves(n.alternate,acc,file);return;}
  if(n.type==='ArrowFunctionExpression'||n.type==='FunctionExpression'){walk.full(n.body,x=>{if(x.type==='Literal'&&typeof x.value==='string'&&/[a-z]{3,} [a-z]/i.test(x.value))acc.push({s:x.value,file});if(x.type==='TemplateLiteral'){const s=x.quasis.map((q,i)=>q.value.cooked+(i<x.expressions.length?'{'+i+'}':'')).join('');if(/[a-z]{3,} [a-z]/i.test(s))acc.push({s,file,tpl:x.expressions.length>0});}});return;}
}
const acc=[];
for(const f of fs.readdirSync(dir).filter(f=>f.endsWith('.js'))){
  const src=fs.readFileSync(path.join(dir,f),'utf8'); let ast;
  try{ast=acorn.parse(src,{ecmaVersion:'latest',sourceType:'script',allowReturnOutsideFunction:true});}catch(e){try{ast=acorn.parse(src,{ecmaVersion:'latest',sourceType:'module'});}catch(e2){console.error('PARSE',f,e2.message);continue;}}
  walk.full(ast,n=>{
    if(n.type==='Property'){const k=n.key&&(n.key.name||n.key.value); if(k==='en') leaves(n.value,acc,f);}
    // tablice [pl,en,es,de,uk] – 5 literałów
    if(n.type==='ArrayExpression'&&n.elements.length===5&&n.elements.every(e=>e&&e.type==='Literal'&&typeof e.value==='string')){acc.push({s:n.elements[1].value,file:f});}
    if(n.type==='AssignmentExpression'&&n.left.type==='MemberExpression'&&n.left.property&&(n.left.property.name==='en')) leaves(n.right,acc,f);
  });
}
fs.writeFileSync(process.argv[3],JSON.stringify(acc));
console.log(acc.length);
