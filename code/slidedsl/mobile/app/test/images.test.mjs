// Fotos da internet (src/pipeline/images.ts) com rede simulada: busca, download, dimensões, crédito e PPTX.
import test from 'node:test';
import assert from 'node:assert/strict';
import JSZip from 'jszip';
import {buildAlto, renderPptx} from '@slidedsl/core';
import {imageSize, base64, resolveImages, searchImages} from '../outputs/tests/pipeline/images.js';

function png(width, height) {
  const b = new Uint8Array(64); b.set([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52]);
  const v = new DataView(b.buffer); v.setUint32(16, width); v.setUint32(20, height); return b;
}
const openverse = {results: [
  {title: 'Tiny icon', url: 'https://x/small.png', foreign_landing_url: 'https://x/p1', creator: 'A', license: 'by', license_url: 'https://cc/by'},
  {title: 'Solar panels on a roof', url: 'https://x/big.png', foreign_landing_url: 'https://x/p2', creator: 'Maria Silva', license: 'by-sa', license_url: 'https://cc/by-sa'},
  {title: 'Not allowed', url: 'https://x/nc.png', license: 'by-nc'}]};
const source = {
  fetchJson: async url => (url.includes('openverse') ? openverse : {collection: {items: []}}),
  fetchBytes: async url => (url.endsWith('small.png') ? png(300, 200) : png(1600, 900)),
};

test('cabeçalho PNG/JPEG e base64', () => {
  assert.deepEqual(imageSize(png(1600, 900)), {mime: 'image/png', width: 1600, height: 900});
  const jpeg = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0, 4, 0, 0, 0xff, 0xc0, 0, 17, 8, 0x02, 0x58, 0x03, 0x20, 3]);
  assert.deepEqual(imageSize(jpeg), {mime: 'image/jpeg', width: 800, height: 600});
  assert.equal(imageSize(new Uint8Array([1, 2, 3])), null);
  assert.equal(base64(new TextEncoder().encode('Olá!')), Buffer.from('Olá!').toString('base64'));
});

test('busca só licenças livres e ordena pelo título', async () => {
  const found = await searchImages('solar panels roof', source.fetchJson);
  assert.deepEqual(found.map(c => c.title), ['Solar panels on a roof', 'Tiny icon']);
  assert.equal(found[0].license, 'CC BY-SA');
});

test('foto pequena é pulada; a grande vai para o slide, o crédito e o PowerPoint', async () => {
  const deck = {title: 'Energia solar', theme: 'claro', slides: [
    {kind: 'capa', title: 'Energia solar em casa'},
    {kind: 'imagem', title: 'Painéis no telhado', image_query: 'solar panels roof', items: [{label: 'Telhado', detail: 'Os painéis ficam voltados para o norte.'}]},
    {kind: 'conclusao', title: 'Avalie o seu telhado', items: [{label: 'Sombra', detail: 'Verifique sombras ao longo do dia.'}, {label: 'Conta', detail: 'Compare o consumo dos últimos meses.'}]}]};
  const media = await resolveImages(deck, source);
  assert.equal(deck.slides[1].image_file, 'foto_2.png');
  assert.equal(media.info['foto_2.png'].width, 1600);
  assert.match(media.data['foto_2.png'], /^data:image\/png;base64,/);
  const built = buildAlto(deck, null, media.info);
  assert.ok(built.ir, JSON.stringify(built.diagnostics.filter(d => d.severity === 'ERRO')));
  const zip = await JSZip.loadAsync(await renderPptx(built.ir, {images: media.data}));
  assert.ok(Object.keys(zip.files).some(f => /^ppt\/media\//.test(f)), 'foto embutida');
  const xml = await zip.file('ppt/slides/slide2.xml').async('string');
  assert.match(xml, /Maria Silva · CC BY-SA/);
});

test('sem foto válida o slide fica sem arquivo (layout de cartões)', async () => {
  const deck = {title: 'X', theme: 'claro', slides: [{kind: 'imagem', title: 'Sem foto', image_query: 'nada', items: []}]};
  const media = await resolveImages(deck, {fetchJson: async () => ({}), fetchBytes: async () => new Uint8Array()});
  assert.equal(deck.slides[0].image_file, undefined);
  assert.equal(media.log[0].result, 'nenhuma foto livre encontrada');
});
