import fs from 'node:fs/promises';
import {checkFixture} from './compare.mjs';
const root=new URL('../../../outputs/parity/',import.meta.url);
const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',root),'utf8'));
const report={passed:0,failed:0,with_ir:manifest.entries.filter(r=>r.has_ir).length,without_ir:manifest.entries.filter(r=>r.status==='exported'&&!r.has_ir).length,excluded:manifest.entries.filter(r=>r.status!=='exported'),unreadable_directories:manifest.unreadable_directories,failures:[]};
for(const row of manifest.entries.filter(r=>r.status==='exported')) {
  let first_difference;
  try {first_difference=await checkFixture(new URL(row.id+'/',root));}
  catch(error){first_difference={error:error.stack};}
  if(first_difference){report.failed++;report.failures.push({id:row.id,source:row.source,first_difference});}else report.passed++;
}
report.rate=report.passed/(report.passed+report.failed);
await fs.writeFile(new URL('relatorio.json',root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,failed:report.failed,rate:report.rate}));
if(report.failed)process.exitCode=1;
