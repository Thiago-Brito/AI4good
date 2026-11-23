import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {checkFixture} from './compare.mjs';
const root=new URL('./fixtures/',import.meta.url);
const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',root),'utf8'));
for(const row of manifest.entries) {
  test(`IR e diagnósticos ${row.id}: ${row.source}`,async()=>assert.equal(await checkFixture(new URL(row.id+'/',root)),null));
}
