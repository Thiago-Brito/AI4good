export function infer_role(id:string,type:string,x:number,y:number,w:number,h:number): [string|null,string|null] {
  if(type==='rectangle'&&x===0&&y===0&&w===1280&&h===720)return ['background','heurística: retângulo do canvas completo'];
  if(id.startsWith('fundo')||id.startsWith('decoracao'))return ['decoracao','heurística: prefixo de ID'];
  if(type==='text'&&id.startsWith('titulo'))return ['titulo','heurística: prefixo titulo'];
  if(type==='text'&&['corpo','subtitulo','vantagem','limitacao','rodape','explicacao'].some(p=>id.startsWith(p)))return ['corpo','heurística: prefixo de ID'];
  return [null,null];
}
