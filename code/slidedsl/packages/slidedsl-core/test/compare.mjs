import fs from 'node:fs/promises';
import {buildAlto} from '../dist/index.js';
export async function readFixture(folder) {
  return Object.fromEntries(await Promise.all(['deck','facts','images','ir','diagnostics'].map(async n=>[n,JSON.parse(await fs.readFile(new URL(n+'.json',folder),'utf8'))])));
}
export function difference(actual,expected,path='$') {
  if(typeof actual==='number'&&typeof expected==='number')return Number.isFinite(actual)&&Math.abs(actual-expected)<=1e-6?null:{path,actual,expected};
  if(actual===expected)return null;
  if(actual===null||expected===null||typeof actual!==typeof expected||typeof actual!=='object')return {path,actual,expected};
  if(Array.isArray(actual)!==Array.isArray(expected))return {path,actual,expected};
  const keys=Object.keys(expected),own=Object.keys(actual);
  if(keys.length!==own.length||keys.some(k=>!own.includes(k)))return {path,actual_keys:own,expected_keys:keys};
  for(const key of keys){const d=difference(actual[key],expected[key],path+(Array.isArray(actual)?`[${key}]`:'.'+key));if(d)return d;}
  return null;
}
export async function checkFixture(folder) {
  const fixture=await readFixture(folder);
  const result=buildAlto(fixture.deck,fixture.facts,fixture.images);
  return difference(result.ir,fixture.ir)??difference(result.diagnostics.map(({code,severity})=>({code,severity})),fixture.diagnostics,'$.diagnostics');
}
