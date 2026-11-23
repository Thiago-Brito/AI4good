import {inflateRawSync} from 'node:zlib';
// Leitor ZIP mínimo para inspeção de artefatos dos dois renderers (sem dependência).
export function slidesInZip(bytes) {
  const buffer=Buffer.from(bytes),result=[];
  let end=buffer.length-22;
  while(end>=0&&buffer.readUInt32LE(end)!==0x06054b50)end--;
  if(end<0)throw Error('ZIP sem diretório central');
  let cursor=buffer.readUInt32LE(end+16);
  for(let i=0;i<buffer.readUInt16LE(end+10);i++) {
    if(buffer.readUInt32LE(cursor)!==0x02014b50)throw Error('Diretório ZIP inválido');
    const method=buffer.readUInt16LE(cursor+10),size=buffer.readUInt32LE(cursor+20);
    const nameLength=buffer.readUInt16LE(cursor+28),extraLength=buffer.readUInt16LE(cursor+30),commentLength=buffer.readUInt16LE(cursor+32);
    const name=buffer.toString('utf8',cursor+46,cursor+46+nameLength),offset=buffer.readUInt32LE(cursor+42);
    if(/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
      const start=offset+30+buffer.readUInt16LE(offset+26)+buffer.readUInt16LE(offset+28);
      const content=buffer.subarray(start,start+size);
      const xml=(method===8?inflateRawSync(content):content).toString('utf8');
      result.push({name,shapes:(xml.match(/<p:sp(?=[\s>])/g)??[]).length,pictures:(xml.match(/<p:pic(?=[\s>])/g)??[]).length,texts:[...xml.matchAll(/<a:t(?:\s[^>]*)?>([\s\S]*?)<\/a:t>/g)].map(m=>m[1])});
    }
    cursor+=46+nameLength+extraLength+commentLength;
  }
  return result.sort((a,b)=>a.name.localeCompare(b.name));
}
