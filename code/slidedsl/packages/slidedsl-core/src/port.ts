// @ts-nocheck

// Gerado por scripts/port_core.py a partir das funções puras do compilador.

import * as __py from './pythonCompat.js';

import { text_width, text_height, optical_size } from './textMetrics.js';

import { analyze, Diagnostic, DSLException, Command, Position, PresentationNode, SlideNode, Element } from './semantic.js';

import rules from './data/design_rules.json' with { type: 'json' };

import themes from './data/themes.json' with { type: 'json' };

function load_rules() { return rules; }

// Fonte: src/slidedsl/geometry.py

function box(...__args) {
var [e] = __py.bind(__args, ["e"], [undefined], false, false);
return [e.x, e.y, __py.bin("Add", e.x, e.width), __py.bin("Add", e.y, e.height)];
}

function intersection(...__args) {
var [a, b] = __py.bind(__args, ["a", "b"], [undefined, undefined], false, false);
var r;
(r = [__py.max(__py.at(a, 0), __py.at(b, 0)), __py.max(__py.at(a, 1), __py.at(b, 1)), __py.min(__py.at(a, 2), __py.at(b, 2)), __py.min(__py.at(a, 3), __py.at(b, 3))]);
return (__py.truth(__py.and([() => (__py.cmp("Gt", __py.at(r, 2), __py.at(r, 0))), () => (__py.cmp("Gt", __py.at(r, 3), __py.at(r, 1)))])) ? r : null);
}

function area(...__args) {
var [r] = __py.bind(__args, ["r"], [undefined], false, false);
return __py.bin("Mult", __py.max(0, __py.bin("Sub", __py.at(r, 2), __py.at(r, 0))), __py.max(0, __py.bin("Sub", __py.at(r, 3), __py.at(r, 1))));
}

function union_area(...__args) {
var [rects] = __py.bind(__args, ["rects"], [undefined], false, false);
var a, b, hi, intervals, left, length, lo, r, right, total, x, xs;

(rects = (() => { let r; const result = []; for (r of __py.iter(rects)) { if (!__py.truth((__py.cmp("Gt", area(r), 0)))) continue; result.push(r); } return result; })());
(xs = __py.sorted((() => { let r, x; const result = []; for (r of __py.iter(rects)) { for (x of __py.iter([__py.at(r, 0), __py.at(r, 2)])) { result.push(x); }} return new Set(result); })()));
(total = 0.0);
for ([left, right] of __py.iter(__py.zip(xs, __py.slice(xs, 1, null, null)))) {
(intervals = __py.sorted((() => { let r; const result = []; for (r of __py.iter(rects)) { if (!__py.truth(__py.and([() => (__py.cmp("Lt", __py.at(r, 0), right)), () => (__py.cmp("Gt", __py.at(r, 2), left))]))) continue; result.push([__py.at(r, 1), __py.at(r, 3)]); } return result; })()));
(length = 0.0);
(lo = null);
(hi = null);
for ([a, b] of __py.iter(intervals)) {
if (__py.truth((__py.cmp("Is", lo, null)))) {
([lo, hi] = [a, b]);
} else {
if (__py.truth((__py.cmp("Gt", a, hi)))) {
length = __py.bin("Add", length, __py.bin("Sub", hi, lo));
([lo, hi] = [a, b]);
} else {
(hi = __py.max(hi, b));
}
}
}
if (__py.truth((__py.cmp("IsNot", lo, null)))) {
length = __py.bin("Add", length, __py.bin("Sub", hi, lo));
}
total = __py.bin("Add", total, __py.bin("Mult", __py.bin("Sub", right, left), length));
}
return total;
}

function distance(...__args) {
var [a, b] = __py.bind(__args, ["a", "b"], [undefined, undefined], false, false);
return __py.math.hypot(__py.max(__py.bin("Sub", __py.at(a, 0), __py.at(b, 2)), __py.bin("Sub", __py.at(b, 0), __py.at(a, 2)), 0), __py.max(__py.bin("Sub", __py.at(a, 1), __py.at(b, 3)), __py.bin("Sub", __py.at(b, 1), __py.at(a, 3)), 0));
}

function bounds(...__args) {
var [elements] = __py.bind(__args, ["elements"], [undefined], false, false);
var e;
return [__py.min((() => { let e; const result = []; for (e of __py.iter(elements)) { result.push(e.x); } return result; })()), __py.min((() => { let e; const result = []; for (e of __py.iter(elements)) { result.push(e.y); } return result; })()), __py.max((() => { let e; const result = []; for (e of __py.iter(elements)) { result.push(__py.bin("Add", e.x, e.width)); } return result; })()), __py.max((() => { let e; const result = []; for (e of __py.iter(elements)) { result.push(__py.bin("Add", e.y, e.height)); } return result; })())];
}

function resolve_position(...__args) {
var [p, size, lookup] = __py.bind(__args, ["p", "size", "lookup"], [undefined, undefined, undefined], false, false);
var ref;
if (__py.truth((__py.cmp("Eq", __py.kind, "absolute")))) {
return [__py.x, __py.y];
}
if (__py.truth((__py.cmp("Eq", __py.kind, "corner")))) {
return [__py.bin("Sub", __py.bin("Sub", 1280, 64), __py.at(size, 0)), 64];
}
(ref = __py.at(lookup, __py.reference));
if (__py.truth((__py.cmp("Eq", __py.kind, "below")))) {
return [ref.x, __py.bin("Add", __py.bin("Add", ref.y, ref.height), __py.margin)];
}
return [__py.bin("Add", __py.bin("Add", ref.x, ref.width), __py.margin), ref.y];
}

function aligned_position(...__args) {
var [a, b, axis] = __py.bind(__args, ["a", "b", "axis"], [undefined, undefined, undefined], false, false);
var x, y;
([x, y] = [__py.at(a, 0), __py.at(a, 1)]);
if (__py.truth((__py.cmp("Eq", axis, "left")))) {
(x = __py.at(b, 0));
} else {
if (__py.truth((__py.cmp("Eq", axis, "right")))) {
(x = __py.bin("Sub", __py.at(b, 2), __py.bin("Sub", __py.at(a, 2), __py.at(a, 0))));
} else {
if (__py.truth((__py.cmp("Eq", axis, "center")))) {
(x = __py.bin("Div", __py.bin("Sub", __py.bin("Add", __py.at(b, 0), __py.at(b, 2)), __py.bin("Sub", __py.at(a, 2), __py.at(a, 0))), 2));
} else {
(y = __py.at(b, 1));
}
}
}
return [x, y];
}

function translate(...__args) {
var [elements, x, y] = __py.bind(__args, ["elements", "x", "y"], [undefined, undefined, undefined], false, false);
var dx, dy, e, r;
(r = bounds(elements));
([dx, dy] = [__py.bin("Sub", x, __py.at(r, 0)), __py.bin("Sub", y, __py.at(r, 1))]);
for (e of __py.iter(elements)) {
e.x = __py.bin("Add", e.x, dx);
e.y = __py.bin("Add", e.y, dy);
}
}

function resize_group(...__args) {
var [elements, width, height] = __py.bind(__args, ["elements", "width", "height"], [undefined, undefined, undefined], false, false);
var e, r, sx, sy;
(r = bounds(elements));
([sx, sy] = [__py.bin("Div", width, __py.bin("Sub", __py.at(r, 2), __py.at(r, 0))), __py.bin("Div", height, __py.bin("Sub", __py.at(r, 3), __py.at(r, 1)))]);
for (e of __py.iter(elements)) {
(e.x = __py.bin("Add", __py.at(r, 0), __py.bin("Mult", __py.bin("Sub", e.x, __py.at(r, 0)), sx)));
(e.y = __py.bin("Add", __py.at(r, 1), __py.bin("Mult", __py.bin("Sub", e.y, __py.at(r, 1)), sy)));
e.width = __py.bin("Mult", e.width, sx);
e.height = __py.bin("Mult", e.height, sy);
}
}

// Fonte: src/slidedsl/editorial.py

var TITLE_PT, LABEL_PT, BODY_PT, CREDIT_PT;
([TITLE_PT, LABEL_PT, BODY_PT, CREDIT_PT] = [42, 24, 20, 12]);

var MIN_TITLE_PT, MIN_LABEL_PT, MIN_BODY_PT, MIN_SUBTITLE_PT;
([MIN_TITLE_PT, MIN_LABEL_PT, MIN_BODY_PT, MIN_SUBTITLE_PT] = [32, 20, 16, 18]);

function proper_words(...__args) {
var [text] = __py.bind(__args, ["text"], [undefined], false, false);
var found, sentence, w;

(found = __py.set());
for (sentence of __py.iter(__py.re.split("[.!?:]\\s+|\\n+", __py.or([() => text, () => ""])))) {
for (w of __py.iter(__py.slice(__py.re.findall("[\\w-]+", sentence), 1, null, null))) {
if (__py.truth(__py.method(__py.slice(w, null, 1, null), "isupper"))) {
__py.method(found, "add", __py.method(w, "casefold"));
}
}
}
return found;
}

var SINGLE_LOWER;
(SINGLE_LOWER = new Set(["A", "O", "E", "À", "É"]));

function sentence_case(...__args) {
var [text, keep] = __py.bind(__args, ["text", "keep"], [undefined, []], false, false);
var c, capitalized, k, long_words, w, words;

(words = __py.method(__py.or([() => text, () => ""]), "split"));
(capitalized = (() => { let w; const result = []; for (w of __py.iter(words)) { if (!__py.truth(__py.and([() => (__py.cmp("Gt", __py.len(w), 3)), () => __py.method(__py.slice(w, null, 1, null), "isupper")]))) continue; result.push(w); } return result; })());
(long_words = (() => { let w; const result = []; for (w of __py.iter(words)) { if (!__py.truth((__py.cmp("Gt", __py.len(w), 3)))) continue; result.push(w); } return result; })());
if (__py.truth(__py.or([() => (__py.cmp("Lt", __py.len(long_words), 2)), () => (__py.cmp("LtE", __py.bin("Div", __py.len(capitalized), __py.len(long_words)), 0.7))]))) {
return text;
}
(keep = (() => { let k; const result = []; for (k of __py.iter(keep)) { result.push(__py.method(k, "casefold")); } return new Set(result); })());
return __py.method(" ", "join", (() => { let k, w; const result = []; for ([k, w] of __py.iter(__py.enumerate(words))) { result.push((__py.truth(__py.or([() => (__py.cmp("Eq", k, 0)), () => __py.and([() => __py.method(w, "isupper"), () => (__py.cmp("NotIn", w, SINGLE_LOWER))]), () => (__py.cmp("In", __py.method(__py.method(w, "strip", ".,:;"), "casefold"), keep)), () => __py.any((() => { let c; const result = []; for (c of __py.iter(__py.slice(w, 1, null, null))) { result.push(__py.method(c, "isupper")); } return result; })())])) ? w : __py.method(w, "lower"))); } return result; })());
}

function capitalize_first(...__args) {
var [text] = __py.bind(__args, ["text"], [undefined], false, false);

if (__py.truth(__py.and([() => text, () => __py.method(__py.at(text, 0), "islower")]))) {
return __py.bin("Add", __py.method(__py.at(text, 0), "upper"), __py.slice(text, 1, null, null));
}
return text;
}

function normalized(...__args) {
var [text] = __py.bind(__args, ["text"], [undefined], false, false);
return __py.method(" ", "join", __py.re.findall("\\w+", __py.method(__py.method(__py.method(__py.unicodedata.normalize("NFKD", __py.or([() => text, () => ""])), "encode", "ascii", "ignore"), "decode"), "casefold")));
}

function distinct_label(...__args) {
var [label, headings] = __py.bind(__args, ["label"], [undefined], true, false);
var h, meaningful, words;

(words = normalized(label));
(meaningful = __py.bin("Sub", __py.set(__py.method(words, "split")), new Set(["a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "na", "no"])));
return __py.bool(__py.and([() => words, () => __py.all((() => { let h; const result = []; for (h of __py.iter(headings)) { result.push(__py.and([() => (__py.cmp("NotEq", words, normalized(h))), () => !__py.truth(__py.and([() => (__py.cmp("GtE", __py.len(meaningful), 2)), () => (__py.cmp("LtE", meaningful, __py.set(__py.method(normalized(h), "split"))))]))])); } return result; })())]));
}

function visible_labels(...__args) {
var [items, headings] = __py.bind(__args, ["items"], [undefined], true, false);
var distinct, i;

(distinct = (() => { let i; const result = []; for (i of __py.iter(items)) { result.push(distinct_label(i.label, ...__py.iter(headings))); } return result; })());
return (() => { let i; const result = []; for (i of __py.iter(items)) { result.push((__py.truth(__py.any(distinct)) ? i.label : null)); } return result; })();
}

function ordered_steps(...__args) {
var [slide] = __py.bind(__args, ["slide"], [undefined], false, false);
var i;
return __py.all((() => { let i; const result = []; for (i of __py.iter(slide.items)) { result.push(__py.re.match("^[\\wáéíóúâêôãõç]+(?:ar|er|ir)\\b", i.label, __py.re.I)); } return result; })());
}

function balanced_title(...__args) {
var [text, width, size, family] = __py.bind(__args, ["text", "width", "size", "family"], [undefined, undefined, TITLE_PT, "Arial"], false, false);
var candidates, cut, line, lines, widths, words;

(words = __py.method(__py.or([() => text, () => ""]), "split"));
if (__py.truth((__py.cmp("LtE", text_width(__py.method(" ", "join", words), size, true, family), __py.bin("Sub", width, 24))))) {
return __py.method(" ", "join", words);
}
(candidates = []);
for (cut of __py.iter(__py.range(2, __py.bin("Sub", __py.len(words), 1)))) {
(lines = [__py.method(" ", "join", __py.slice(words, null, cut, null)), __py.method(" ", "join", __py.slice(words, cut, null, null))]);
(widths = (() => { let line; const result = []; for (line of __py.iter(lines)) { result.push(text_width(line, size, true, family)); } return result; })());
if (__py.truth((__py.cmp("LtE", __py.max(widths), __py.bin("Sub", width, 24))))) {
__py.method(candidates, "append", [__py.abs(__py.bin("Sub", __py.at(widths, 0), __py.at(widths, 1))), __py.method("\n", "join", lines)]);
}
}
return (__py.truth(candidates) ? __py.at(__py.min(candidates), 1) : text);
}

function composition(...__args) {
var [slide, deck, index] = __py.bind(__args, ["slide", "deck", "index"], [undefined, undefined, undefined], false, false);
var i, previous;

if (__py.truth(__py.and([() => (__py.cmp("Eq", slide.kind, "etapas")), () => !__py.truth(ordered_steps(slide))]))) {
return "rows";
}
if (__py.truth((__py.cmp("NotEq", slide.kind, "topicos")))) {
return slide.kind;
}
if (__py.truth((__py.cmp("Gt", __py.len(slide.items), 3)))) {
return "rows";
}
(previous = (__py.truth(index) ? __py.at(deck.slides, __py.bin("Sub", index, 1)) : null));
if (__py.truth(__py.and([() => previous, () => (__py.cmp("Eq", previous.kind, "topicos"))]))) {
return (__py.truth((__py.cmp("Eq", composition(previous, deck, __py.bin("Sub", index, 1)), "cards"))) ? "rows" : "cards");
}
if (__py.truth((__py.cmp("Gt", __py.max((() => { let i; const result = []; for (i of __py.iter(slide.items)) { result.push(__py.len(__py.or([() => i.detail, () => ""]))); } return result; })(), __py.kw({default: 0})), 100)))) {
return "rows";
}
return (__py.truth((__py.cmp("Lt", __py.sum((() => { let i; const result = []; for (i of __py.iter(slide.items)) { result.push(__py.len(i.label)); } return result; })()), 65))) ? "cards" : "rows");
}

// Fonte: src/slidedsl/design_system.py

var WIDTH, HEIGHT, MARGIN, RIGHT;
([WIDTH, HEIGHT, MARGIN, RIGHT] = [1280, 720, 64, 1216]);

var GUTTER;
(GUTTER = 24);

var SPACES;
(SPACES = [8, 16, 24, 32, 48, 64]);

var XS, SM, MD, LG, XL, XXL;
([XS, SM, MD, LG, XL, XXL] = SPACES);

var TITLE_Y;
(TITLE_Y = MARGIN);

var CONTENT_BOTTOM;
(CONTENT_BOTTOM = 636);

var CARD_PADDING;
(CARD_PADDING = LG);

var LABEL_GAP;
(LABEL_GAP = 12);

var RULE;
(RULE = 4);

var OPTICAL_CENTER;
(OPTICAL_CENTER = 0.44);

var MIN_BLOCK_FRACTION;
(MIN_BLOCK_FRACTION = 0.6);

var OPTICAL_LABEL_PT;
(OPTICAL_LABEL_PT = 23.5);

var COL_WIDTH;
(COL_WIDTH = __py.bin("Div", __py.bin("Sub", __py.bin("Sub", RIGHT, MARGIN), __py.bin("Mult", 11, GUTTER)), 12));

function card_position(...__args) {
var [top, natural_height, bottom] = __py.bind(__args, ["top", "natural_height", "bottom"], [undefined, undefined, CONTENT_BOTTOM], false, false);
var available;

(available = __py.bin("Sub", bottom, top));
return __py.bin("Add", top, __py.max(0, __py.bin("Sub", __py.bin("Div", __py.bin("Sub", available, natural_height), 2), __py.bin("Mult", 0.05, available))));
}

function col(...__args) {
var [i, span] = __py.bind(__args, ["i", "span"], [undefined, 1], false, false);

if (__py.truth(__py.or([() => (__py.cmp("Lt", i, 0)), () => (__py.cmp("Lt", span, 1)), () => (__py.cmp("Gt", __py.bin("Add", i, span), 12))]))) {
throw new Error("Coluna/span fora da grade de 12 colunas.");
}
return [__py.bin("Add", MARGIN, __py.bin("Mult", i, __py.bin("Add", COL_WIDTH, GUTTER))), __py.bin("Add", __py.bin("Mult", span, COL_WIDTH), __py.bin("Mult", __py.bin("Sub", span, 1), GUTTER))];
}

function distribute(...__args) {
var [top, natural_height, count, bottom] = __py.bind(__args, ["top", "natural_height", "count", "bottom"], [undefined, undefined, 1, CONTENT_BOTTOM], false, false);
var available, height, target;
(available = __py.max(1, __py.bin("Sub", bottom, top)));
(target = __py.max(natural_height, (__py.truth((__py.cmp("GtE", count, 2))) ? __py.bin("Mult", available, MIN_BLOCK_FRACTION) : natural_height)));
(height = __py.min(available, target));
return [__py.bin("Add", top, __py.bin("Mult", __py.max(0, __py.bin("Sub", available, height)), OPTICAL_CENTER)), height];
}

class Estilo {
constructor(...args) {
const values = __py.bind(args, ["comum", "destaque", "tema", "fonte_titulo", "fonte_corpo", "raio", "cartao", "marcador", "alinhamento_titulo", "motivo_capa", "margem_vertical"], [undefined, undefined, undefined, "Calibri", "Calibri", 0, "preenchido", "barra", "left", "lateral", false]);
Object.assign(this, Object.fromEntries(["comum", "destaque", "tema", "fonte_titulo", "fonte_corpo", "raio", "cartao", "marcador", "alinhamento_titulo", "motivo_capa", "margem_vertical"].map((n,i) => [n,values[i]])));
}

}

function title_style(...__args) {
var [element, background] = __py.bind(__args, ["element", "background"], [undefined, undefined], false, false);
var palette, size, style;



if (__py.truth(!__py.truth(__py.re.fullmatch("s\\d+_(titulo|transicao)_\\d+", element.id)))) {
return null;
}
for (style of __py.iter(__py.method(STYLES, "values"))) {
for (palette of __py.iter([style.comum, style.destaque])) {
if (__py.truth(__py.and([() => (__py.cmp("Eq", element.font_face, style.fonte_titulo)), () => background, () => (__py.cmp("Eq", __py.method(background, "upper"), __py.method(__py.at(palette, "bg"), "upper")))]))) {

(size = (__py.truth((__py.cmp("In", "_transicao_", element.id))) ? __py.min(54, optical_size(48, style.fonte_titulo, 32)) : optical_size(42, style.fonte_titulo, 32)));
return [size, __py.at(palette, "text"), style.fonte_titulo];
}
}
}
return null;
}

// Fonte: src/slidedsl/design_rules.py

function luminance(...__args) {
var [color] = __py.bind(__args, ["color"], [undefined], false, false);
var c, linear, n, v, values, weight;
(values = (() => { let n; const result = []; for (n of __py.iter([1, 3, 5])) { result.push(__py.bin("Div", __py.int(__py.slice(color, n, __py.bin("Add", n, 2), null), 16), 255)); } return result; })());
(linear = (() => { let v; const result = []; for (v of __py.iter(values)) { result.push((__py.truth((__py.cmp("LtE", v, 0.04045))) ? __py.bin("Div", v, 12.92) : __py.bin("Pow", __py.bin("Div", __py.bin("Add", v, 0.055), 1.055), 2.4))); } return result; })());
return __py.sum((() => { let c, weight; const result = []; for ([c, weight] of __py.iter(__py.zip(linear, [0.2126, 0.7152, 0.0722]))) { result.push(__py.bin("Mult", c, weight)); } return result; })());
}

function contrast(...__args) {
var [a, b] = __py.bind(__args, ["a", "b"], [undefined, undefined], false, false);
var high, low;
([low, high] = __py.sorted([luminance(a), luminance(b)]));
return __py.bin("Div", __py.bin("Add", high, 0.05), __py.bin("Add", low, 0.05));
}

function known_background(...__args) {
var [text, elements, defaultValue] = __py.bind(__args, ["text", "elements", "default"], [undefined, undefined, undefined], false, false);
var e, r;
(r = box(text));
for (e of __py.iter(__py.sorted(elements, __py.kw({key: (e) => e.z, reverse: true})))) {
if (__py.truth(__py.or([() => (__py.cmp("GtE", e.z, text.z)), () => (__py.cmp("Eq", e.type, "text")), () => !__py.truth(intersection(r, box(e)))]))) {
continue;
}
if (__py.truth(__py.or([() => (__py.cmp("NotEq", e.type, "rectangle")), () => (__py.cmp("NotEq", intersection(r, box(e)), r))]))) {
return null;
}
return e.color;
}
return defaultValue;
}

function estimated_overflow(...__args) {
var [e, cfg] = __py.bind(__args, ["e", "cfg"], [undefined, undefined], false, false);
var capacity, font_px, height, line, lines, longest, measured, needed, w, width;

(width = __py.max(0, __py.bin("Sub", e.width, __py.bin("Mult", 2, __py.at(cfg, "text_padding")))));
(height = __py.max(0, __py.bin("Sub", e.height, __py.bin("Mult", 2, __py.at(cfg, "text_padding")))));
(font_px = __py.bin("Div", __py.bin("Mult", __py.or([() => e.font_size, () => 24]), 96), 72));
(capacity = __py.max(1, __py.math.floor(__py.bin("Div", width, __py.bin("Mult", __py.at(cfg, "character_width_factor"), font_px)))));
(lines = __py.sum((() => { let line; const result = []; for (line of __py.iter(__py.method(__py.or([() => e.text, () => ""]), "split", "\n"))) { result.push(__py.max(1, __py.math.ceil(__py.bin("Div", __py.len(line), capacity)))); } return result; })()));
(needed = __py.bin("Mult", __py.bin("Mult", lines, font_px), __py.at(cfg, "line_height_factor")));
(measured = text_height(__py.or([() => e.text, () => ""]), e.width, __py.or([() => e.font_size, () => 24]), e.bold, e.font_face));
(longest = __py.max((() => { let w; const result = []; for (w of __py.iter(__py.method(__py.or([() => e.text, () => ""]), "split"))) { result.push(text_width(w, __py.or([() => e.font_size, () => 24]), e.bold, e.font_face)); } return result; })(), __py.kw({default: 0})));
return ({["estimated_lines"]: lines, ["estimated_height"]: (__py.truth((__py.cmp("Eq", e.font_face, "Arial"))) ? __py.max(needed, __py.bin("Sub", measured, 18)) : __py.bin("Sub", measured, 18)), ["available_height"]: height, ["longest_word"]: longest, ["available_width"]: width, ["font_family"]: e.font_face, ["characters_per_line"]: capacity, ["approximation"]: "AABB; quebra por família/Pillow com margem; Arial mantém piso por caracteres"});
}

function check_design(...__args) {
var [deck, config] = __py.bind(__args, ["deck", "config"], [undefined, null], false, false);
var a, actual, axis, b, bg, bodies, by_id, cfg, clipped, covered, delta, density, ds, e, estimate, expected, fraction, g, group_map, id, largest, members, occupied, own_background, r, ratio, s, theme, titles, up, valid, worst;
(cfg = __py.or([() => config, () => load_rules()]));
(theme = __py.at(themes, deck.theme));
(ds = []);
for (s of __py.iter(deck.slides)) {
function emit(...__args) {
var [code, message, e, evidence, suggestion, info] = __py.bind(__args, ["code", "message", "e", "evidence", "suggestion", "info"], [undefined, undefined, null, null, "Revise a composição.", false], false, false);
__py.method(ds, "append", Diagnostic(__py.kw({code: code, severity: (__py.truth(info) ? "INFORMAÇÃO" : __py.at(__py.at(cfg, "severities"), code)), message: message, slide: s.number, element: (__py.truth(e) ? e.id : null), line: (__py.truth(e) ? e.source_line : null), column: (__py.truth(e) ? e.source_column : null), evidence: ({...(__py.truth(e) ? ({["x"]: e.x, ["y"]: e.y, ["width"]: e.width, ["height"]: e.height}) : ({})), ...__py.or([() => evidence, () => ({})])}), suggestion: suggestion})));
}
(valid = (() => { let e; const result = []; for (e of __py.iter(s.elements)) { if (!__py.truth(__py.and([() => (__py.cmp("Gt", e.width, 0)), () => (__py.cmp("Gt", e.height, 0))]))) continue; result.push(e); } return result; })());
(by_id = (() => { let e; const result = []; for (e of __py.iter(valid)) { result.push([e.id, e]); } return Object.fromEntries(result); })());
(group_map = (() => { let g; const result = []; for (g of __py.iter(s.groups)) { result.push([g.id, g]); } return Object.fromEntries(result); })());
function object_box(...__args) {
var [id] = __py.bind(__args, ["id"], [undefined], false, false);
var m;
if (__py.truth((__py.cmp("In", id, by_id)))) {
return box(__py.at(by_id, id));
}
if (__py.truth(__py.and([() => (__py.cmp("In", id, group_map)), () => __py.all((() => { let m; const result = []; for (m of __py.iter(__py.at(group_map, id).members)) { result.push((__py.cmp("In", m, by_id))); } return result; })())]))) {
return bounds((() => { let m; const result = []; for (m of __py.iter(__py.at(group_map, id).members)) { result.push(__py.at(by_id, m)); } return result; })());
}
return null;
}
for (e of __py.iter(s.elements)) {
if (__py.truth(__py.or([() => (__py.cmp("LtE", e.width, 0)), () => (__py.cmp("LtE", e.height, 0))]))) {
emit("D009", "Largura ou altura não positiva.", e, __py.kw({suggestion: "Defina dimensões maiores que zero."}));
continue;
}
if (__py.truth(__py.or([() => (__py.cmp("Lt", e.x, 0)), () => (__py.cmp("Lt", e.y, 0)), () => (__py.cmp("Gt", __py.bin("Add", e.x, e.width), 1280)), () => (__py.cmp("Gt", __py.bin("Add", e.y, e.height), 720))]))) {
emit("D001", "Elemento sai do canvas 1280×720.", e, __py.kw({suggestion: "Mova ou redimensione o elemento para dentro da tela."}));
}
if (__py.truth((__py.cmp("Eq", e.type, "text")))) {
if (__py.truth(__py.and([() => (__py.cmp("Eq", e.role, "corpo")), () => (__py.cmp("Lt", __py.or([() => e.font_size, () => 24]), 16))]))) {
emit("D006", "Corpo abaixo do mínimo legível de 16 pt.", e, ({["minimum"]: 16, ["actual"]: e.font_size}), "Encurte o texto antes de reduzir a fonte.");
}
(bg = known_background(e, valid, __py.at(__py.at(theme, "colors"), "fundo")));
if (__py.truth((__py.cmp("Is", bg, null)))) {
emit("D002", "Contraste INDETERMINADO: fundo contém imagem, elipse ou cores parciais.", e, ({["status"]: "INDETERMINADO"}), "Use fundo sólido conhecido para medir contraste.", __py.kw({info: true}));
} else {
if (__py.truth(e.color)) {
(ratio = contrast(e.color, bg));
if (__py.truth((__py.cmp("Lt", ratio, __py.at(cfg, "contrast_minimum"))))) {
emit("D002", "Contraste abaixo do mínimo configurado.", e, ({["ratio"]: ratio, ["minimum"]: __py.at(cfg, "contrast_minimum"), ["background"]: bg}), "Aumente a diferença de luminância entre texto e fundo.");
}
}
}
if (__py.truth((__py.cmp("Eq", e.role, "titulo")))) {
(actual = [e.font_size, e.color, e.font_face]);
(expected = [__py.at(__py.at(theme, "fonts"), "titulo"), __py.at(__py.at(theme, "colors"), "texto"), __py.at(theme, "font_face")]);

(expected = __py.or([() => title_style(e, bg), () => expected]));
(own_background = __py.and([() => (__py.cmp("IsNot", bg, null)), () => (__py.cmp("NotEq", __py.method(bg, "upper"), __py.method(__py.at(__py.at(theme, "colors"), "fundo"), "upper")))]));
if (__py.truth(own_background)) {
(expected = [__py.at(expected, 0), e.color, __py.at(expected, 2)]);
}
if (__py.truth((__py.cmp("NotEq", actual, expected)))) {
emit("D003", "Título diverge da fonte/tamanho/cor do tema.", e, ({["actual"]: actual, ["expected"]: expected, ["role_origin"]: e.role_origin}), "Use os tokens titulo e texto do tema ou justifique a variação.");
}
}
(estimate = estimated_overflow(e, cfg));
if (__py.truth(__py.or([() => (__py.cmp("Gt", __py.at(estimate, "estimated_height"), __py.at(estimate, "available_height"))), () => (__py.cmp("Gt", __py.at(estimate, "longest_word"), __py.at(estimate, "available_width")))]))) {
emit("D010", "Possível overflow de texto (estimativa aproximada).", e, estimate, "Amplie a caixa, reduza o conteúdo ou a fonte; confira no PowerPoint.");
}
}
if (__py.truth((__py.cmp("NotIn", e.role, new Set(["background", "decoracao"]))))) {
(clipped = (() => { let up; const result = []; for (up of __py.iter(valid)) { if (!__py.truth(__py.and([() => (__py.cmp("Gt", up.z, e.z)), () => (__py.cmp("NotEq", up.type, "text"))]))) continue; result.push(intersection(box(e), box(up))); } return result; })());
(covered = union_area((() => { let r; const result = []; for (r of __py.iter(clipped)) { if (!__py.truth(r)) continue; result.push(r); } return result; })()));
(fraction = __py.bin("Div", covered, area(box(e))));
if (__py.truth((__py.cmp("Gt", fraction, __py.at(cfg, "occlusion_maximum"))))) {
emit("D008", "Elemento relevante encoberto por objetos em camadas superiores.", e, ({["covered_area"]: covered, ["fraction"]: fraction, ["maximum"]: __py.at(cfg, "occlusion_maximum"), ["approximation"]: "caixas retangulares; texto transparente não cobre caixa inteira"}), "Traga o objeto para frente, reduza a interseção ou anote o papel decorativo.");
}
}
}
for (r of __py.iter(s.relations)) {
if (__py.truth((__py.cmp("In", r.kind, new Set(["below", "right"]))))) {
continue;
}
([a, b] = [object_box(r.target), object_box(r.reference)]);
if (__py.truth(__py.or([() => (__py.cmp("Is", a, null)), () => (__py.cmp("Is", b, null))]))) {
continue;
}
(axis = __py.at(({["left"]: [__py.at(a, 0), __py.at(b, 0)], ["align_right"]: [__py.at(a, 2), __py.at(b, 2)], ["center"]: [__py.bin("Div", __py.bin("Add", __py.at(a, 0), __py.at(a, 2)), 2), __py.bin("Div", __py.bin("Add", __py.at(b, 0), __py.at(b, 2)), 2)], ["top"]: [__py.at(a, 1), __py.at(b, 1)]}), r.kind));
(delta = __py.abs(__py.bin("Sub", __py.at(axis, 0), __py.at(axis, 1))));
if (__py.truth((__py.cmp("Gt", delta, __py.at(cfg, "alignment_tolerance"))))) {
emit("D004", "Alinhamento declarado tem desvio acima da tolerância.", __py.method(by_id, "get", r.target), ({["target"]: r.target, ["reference"]: r.reference, ["axis"]: r.kind, ["delta"]: delta, ["tolerance"]: __py.at(cfg, "alignment_tolerance")}), "Execute novamente alinhar ou corrija as coordenadas.");
(__py.at(ds, -(1)).element = r.target);
(__py.at(ds, -(1)).line = r.source_line);
(__py.at(ds, -(1)).column = r.source_column);
}
}
for (g of __py.iter(s.groups)) {
(members = (() => { let id; const result = []; for (id of __py.iter(g.members)) { if (!__py.truth((__py.cmp("In", id, by_id)))) continue; result.push(__py.at(by_id, id)); } return result; })());
(worst = __py.max((() => { let a, b; const result = []; for ([a, b] of __py.iter(__py.combinations(members, 2))) { result.push(distance(box(a), box(b))); } return result; })(), __py.kw({default: 0})));
if (__py.truth((__py.cmp("Gt", worst, __py.at(cfg, "proximity_maximum"))))) {
emit("D005", "Integrantes do grupo muito distantes.", __py.kw({evidence: ({["group"]: g.id, ["maximum_gap"]: worst, ["threshold"]: __py.at(cfg, "proximity_maximum")}), suggestion: "Aproxime os membros ou reorganize os grupos."}));
(__py.at(ds, -(1)).element = g.id);
(__py.at(ds, -(1)).line = g.source_line);
}
}
(titles = (() => { let e; const result = []; for (e of __py.iter(valid)) { if (!__py.truth(__py.and([() => (__py.cmp("Eq", e.type, "text")), () => (__py.cmp("Eq", e.role, "titulo"))]))) continue; result.push(e); } return result; })());
(bodies = (() => { let e; const result = []; for (e of __py.iter(valid)) { if (!__py.truth(__py.and([() => (__py.cmp("Eq", e.type, "text")), () => (__py.cmp("Eq", e.role, "corpo"))]))) continue; result.push(e); } return result; })());
if (__py.truth(bodies)) {
(largest = __py.max((() => { let e; const result = []; for (e of __py.iter(bodies)) { result.push(__py.or([() => e.font_size, () => 0])); } return result; })()));
for (e of __py.iter(titles)) {
if (__py.truth((__py.cmp("Lt", __py.or([() => e.font_size, () => 0]), largest)))) {
emit("D006", "Título menor que texto de corpo conhecido.", e, ({["body_font_size"]: largest}), "Aumente o título ou reduza o corpo.");
}
}
}
(occupied = (() => { let e; const result = []; for (e of __py.iter(valid)) { if (!__py.truth((__py.cmp("NotEq", e.role, "background")))) continue; result.push(intersection(box(e), [0, 0, 1280, 720])); } return result; })());
(density = __py.bin("Div", union_area((() => { let r; const result = []; for (r of __py.iter(occupied)) { if (!__py.truth(r)) continue; result.push(r); } return result; })()), __py.bin("Mult", 1280, 720)));
if (__py.truth((__py.cmp("Gt", density, __py.at(cfg, "density_maximum"))))) {
emit("D007", "Densidade aproximada acima do limite; não mede beleza.", __py.kw({evidence: ({["fraction"]: density, ["threshold"]: __py.at(cfg, "density_maximum"), ["approximation"]: "união de caixas, incluindo decoração e caixas de texto"}), suggestion: "Reduza a ocupação e crie mais espaço livre."}));
}
}
return ds;
}

// Fonte: src/slidedsl/layout_score.py

var WEIGHTS;
(WEIGHTS = __py.dict(__py.kw({ocupacao: 0.35, equilibrio: 0.2, alinhamento: 0.15, regularidade: 0.15, ritmo: 0.15})));

var BLOCKERS;
(BLOCKERS = new Set(["A010", "A019", "D001", "D002", "D008", "D010"]));

function occupancy(...__args) {
var [boxes, region] = __py.bind(__args, ["boxes", "region"], [undefined, undefined], false, false);
var b, clipped, r;
(clipped = (() => { let b, r; const result = []; for (b of __py.iter(boxes)) { if (!__py.truth((r = intersection(b, region)))) continue; result.push(r); } return result; })());
return __py.min(1.0, __py.bin("Div", union_area(clipped), __py.max(1, area(region))));
}

function occupation_score(...__args) {
var [fraction] = __py.bind(__args, ["fraction"], [undefined], false, false);
if (__py.truth((__py.cmp("LtE", 0.55, fraction) && __py.cmp("LtE", fraction, 0.78)))) {
return 1.0;
}
if (__py.truth((__py.cmp("Lt", fraction, 0.45)))) {
return __py.max(0.0, __py.bin("Mult", 0.8, __py.bin("Pow", __py.bin("Div", fraction, 0.45), 2)));
}
return __py.max(0.0, __py.min(1.0, __py.bin("Add", 0.8, __py.bin("Mult", 2, __py.bin("Sub", fraction, 0.45))), __py.bin("Div", __py.bin("Sub", 1, fraction), 0.22)));
}

function balance(...__args) {
var [boxes, region, weights] = __py.bind(__args, ["boxes", "region", "weights"], [undefined, undefined, null], false, false);
var b, cx, cy, m, masses, rx, ry, total, w;
if (__py.truth(!__py.truth(boxes))) {
return 0.0;
}
(weights = __py.or([() => weights, () => __py.bin("Mult", [1.0], __py.len(boxes))]));
(masses = (() => { let b, w; const result = []; for ([b, w] of __py.iter(__py.zip(boxes, weights))) { result.push(__py.bin("Mult", area(b), w)); } return result; })());
(total = __py.sum(masses));
if (__py.truth((__py.cmp("LtE", total, 0)))) {
return 0.0;
}
(cx = __py.bin("Div", __py.sum((() => { let b, m; const result = []; for ([b, m] of __py.iter(__py.zip(boxes, masses))) { result.push(__py.bin("Mult", __py.bin("Div", __py.bin("Add", __py.at(b, 0), __py.at(b, 2)), 2), m)); } return result; })()), total));
(cy = __py.bin("Div", __py.sum((() => { let b, m; const result = []; for ([b, m] of __py.iter(__py.zip(boxes, masses))) { result.push(__py.bin("Mult", __py.bin("Div", __py.bin("Add", __py.at(b, 1), __py.at(b, 3)), 2), m)); } return result; })()), total));
([rx, ry] = [__py.bin("Div", __py.bin("Add", __py.at(region, 0), __py.at(region, 2)), 2), __py.bin("Div", __py.bin("Add", __py.at(region, 1), __py.at(region, 3)), 2)]);
return __py.max(0.0, __py.bin("Sub", 1, __py.bin("Div", __py.math.hypot(__py.bin("Sub", cx, rx), __py.bin("Sub", cy, ry)), __py.max(1, __py.bin("Div", __py.math.hypot(__py.bin("Sub", __py.at(region, 2), __py.at(region, 0)), __py.bin("Sub", __py.at(region, 3), __py.at(region, 1))), 2)))));
}

function alignment(...__args) {
var [boxes, tolerance] = __py.bind(__args, ["boxes", "tolerance"], [undefined, 2], false, false);
var b;
if (__py.truth((__py.cmp("Lt", __py.len(boxes), 2)))) {
return 1.0;
}
function distinct(...__args) {
var [values] = __py.bind(__args, ["values"], [undefined], false, false);
var anchors, v;
(anchors = []);
for (v of __py.iter(__py.sorted(values))) {
if (__py.truth(__py.or([() => !__py.truth(anchors), () => (__py.cmp("Gt", __py.bin("Sub", v, __py.at(anchors, -(1))), tolerance))]))) {
__py.method(anchors, "append", v);
}
}
return __py.len(anchors);
}
return __py.bin("Sub", 1, __py.bin("Div", __py.bin("Sub", __py.bin("Add", distinct((() => { let b; const result = []; for (b of __py.iter(boxes)) { result.push(__py.at(b, 0)); } return result; })()), distinct((() => { let b; const result = []; for (b of __py.iter(boxes)) { result.push(__py.at(b, 1)); } return result; })())), 2), __py.bin("Mult", 2, __py.len(boxes))));
}

function regularity(...__args) {
var [boxes] = __py.bind(__args, ["boxes"], [undefined], false, false);
var a, b, gaps, heights, ordered, widths;

if (__py.truth((__py.cmp("Lt", __py.len(boxes), 2)))) {
return 1.0;
}
(widths = (() => { let b; const result = []; for (b of __py.iter(boxes)) { result.push(__py.bin("Sub", __py.at(b, 2), __py.at(b, 0))); } return result; })());
(heights = (() => { let b; const result = []; for (b of __py.iter(boxes)) { result.push(__py.bin("Sub", __py.at(b, 3), __py.at(b, 1))); } return result; })());
(ordered = __py.sorted(boxes, __py.kw({key: (b) => [__py.at(b, 1), __py.at(b, 0)]})));
(gaps = (() => { let a, b; const result = []; for ([a, b] of __py.iter(__py.zip(ordered, __py.slice(ordered, 1, null, null)))) { result.push((__py.truth((__py.cmp("LtE", __py.abs(__py.bin("Sub", __py.at(a, 1), __py.at(b, 1))), 2))) ? __py.max(0, __py.bin("Sub", __py.at(b, 0), __py.at(a, 2))) : __py.max(0, __py.bin("Sub", __py.at(b, 1), __py.at(a, 3))))); } return result; })());
function cv(...__args) {
var [values] = __py.bind(__args, ["values"], [undefined], false, false);
return (__py.truth(values) ? __py.bin("Div", __py.pstdev(values), __py.max(1, __py.bin("Div", __py.sum(values), __py.len(values)))) : 0);
}
return __py.bin("Div", 1, __py.bin("Add", __py.bin("Add", __py.bin("Add", 1, cv(widths)), cv(heights)), cv(gaps)));
}

function rhythm(...__args) {
var [variant, previous, visual, previous_visual, history] = __py.bind(__args, ["variant", "previous", "visual", "previous_visual", "history"], [undefined, undefined, null, null, []], false, false);
if (__py.truth((__py.cmp("Eq", variant, previous)))) {
return 0.1;
}
if (__py.truth((__py.cmp("In", variant, __py.slice(history, -(3), null, null))))) {
return 0.45;
}
if (__py.truth(__py.and([() => (__py.cmp("IsNot", visual, null)), () => (__py.cmp("Eq", visual, previous_visual))]))) {
return 0.55;
}
return 1.0;
}

function aggregate(...__args) {
var [scores] = __py.bind(__args, ["scores"], [undefined], false, false);
var k, w;
return __py.bin("Pow", __py.sum((() => { let k, w; const result = []; for ([k, w] of __py.iter(__py.method(WEIGHTS, "items"))) { result.push(__py.bin("Mult", w, __py.bin("Pow", __py.max(0.01, __py.at(scores, k)), -(2)))); } return result; })()), -(0.5));
}

function useful_elements(...__args) {
var [slide] = __py.bind(__args, ["slide"], [undefined], false, false);
var e;
return (() => { let e; const result = []; for (e of __py.iter(slide.elements)) { if (!__py.truth(__py.or([() => __py.and([() => (__py.cmp("Eq", e.type, "text")), () => (__py.cmp("NotEq", e.role, "titulo")), () => (__py.cmp("GtE", __py.or([() => e.font_size, () => 0]), 16))]), () => (__py.cmp("Eq", e.type, "image")), () => (__py.cmp("In", "_card_", e.id)), () => (__py.cmp("In", "_cabecalho_", e.id))]))) continue; result.push(e); } return result; })();
}

function score_slide(...__args) {
var [slide, variant, previous, visual, previous_visual, history] = __py.bind(__args, ["slide", "variant", "previous", "visual", "previous_visual", "history"], [undefined, undefined, null, null, null, []], false, false);
var _, boxes, clipped, distinct, diversity_bonus, e, elements, fraction, g, groups, key, r, region, scores, top, weights;
(top = __py.max((() => { let e; const result = []; for (e of __py.iter(slide.elements)) { if (!__py.truth((__py.cmp("Eq", e.role, "titulo")))) continue; result.push(__py.bin("Add", __py.bin("Add", e.y, e.height), 16)); } return result; })(), __py.kw({default: 64})));
(region = [64, __py.min(top, 635), 1216, 636]);
(elements = useful_elements(slide));
(clipped = (() => { let e, r; const result = []; for (e of __py.iter(elements)) { if (!__py.truth((r = intersection(box(e), region)))) continue; result.push([e, r]); } return result; })());
(boxes = (() => { let _, r; const result = []; for ([_, r] of __py.iter(clipped)) { result.push(r); } return result; })());

(weights = (() => { let _, e; const result = []; for ([e, _] of __py.iter(clipped)) { result.push((__py.truth((__py.cmp("Eq", e.type, "image"))) ? 1.2 : (__py.truth((__py.cmp("Eq", e.type, "text"))) ? __py.bin("Add", 0.8, __py.bin("Mult", 0.4, __py.bin("Sub", 1, luminance(__py.or([() => e.color, () => "#000000"]))))) : (__py.truth((__py.cmp("LtE", e.height, 8))) ? 0.08 : 0.65)))); } return result; })());
(groups = ({}));
for ([e, r] of __py.iter(clipped)) {
(key = [e.type, (__py.truth((__py.cmp("In", "_rotulo_", e.id))) ? "rotulo" : (__py.truth((__py.cmp("In", "_detalhe_", e.id))) ? "detalhe" : __py.at(__py.method(e.id, "split", "_"), 1)))]);
__py.method(__py.method(groups, "setdefault", key, []), "append", r);
}
(fraction = occupancy(boxes, region));
(scores = __py.dict(__py.kw({ocupacao: occupation_score(fraction), equilibrio: balance(boxes, region, weights), alinhamento: alignment(boxes), regularidade: __py.bin("Div", __py.sum((() => { let g; const result = []; for (g of __py.iter(__py.method(groups, "values"))) { result.push(regularity(g)); } return result; })()), __py.max(1, __py.len(groups))), ritmo: rhythm(variant, previous, visual, previous_visual, history)})));
(distinct = __py.len(__py.bin("BitOr", __py.set(history), new Set([variant]))));
(diversity_bonus = __py.bin("Div", __py.bin("Mult", 0.03, distinct), __py.max(1, __py.bin("Add", __py.len(history), 1))));
return __py.dict(__py.kw({variant: variant, visual: visual, occupancy: fraction, scores: scores, diversity_bonus: diversity_bonus, score: __py.min(1.0, __py.bin("Add", aggregate(scores), diversity_bonus))}));
}

function content_preference(...__args) {
var [metrics, kind, items] = __py.bind(__args, ["metrics", "kind", "items"], [undefined, undefined, undefined], false, false);
var bonus, compact, i, result;

(result = __py.dict(metrics));
(compact = __py.and([() => (__py.cmp("LtE", 2, __py.len(items)) && __py.cmp("LtE", __py.len(items), 3)), () => __py.all((() => { let i; const result = []; for (i of __py.iter(items)) { result.push(__py.and([() => (__py.cmp("LtE", __py.len(i.label), 36)), () => (__py.cmp("LtE", __py.len(__py.or([() => i.detail, () => ""])), 110))])); } return result; })())]));
(bonus = (__py.truth(__py.and([() => (__py.cmp("Eq", kind, "topicos")), () => compact, () => __py.method(__py.at(metrics, "variant"), "startswith", "cards")])) ? 0.08 : 0.0));
if (__py.truth(__py.and([() => (__py.cmp("Eq", kind, "conclusao")), () => (__py.cmp("Eq", __py.at(metrics, "variant"), "actions_columns"))]))) {
(bonus = 0.12);
}
(result["content_bonus"] = bonus);
(result["score"] = __py.min(1.0, __py.bin("Add", __py.at(result, "score"), bonus)));
if (__py.truth(__py.and([() => (__py.cmp("Eq", kind, "topicos")), () => compact, () => (__py.cmp("Eq", __py.at(metrics, "variant"), "rows"))]))) {
(result["score"] = __py.min(0.7, __py.at(result, "score")));
}
if (__py.truth(__py.and([() => (__py.cmp("Eq", kind, "conclusao")), () => (__py.cmp("Eq", __py.at(metrics, "variant"), "actions_rows"))]))) {
(result["score"] = __py.min(0.65, __py.at(result, "score")));
}
return result;
}

function choose(...__args) {
var [candidates, previous] = __py.bind(__args, ["candidates", "previous"], [undefined, null], false, false);
var c, pool, valid;

(valid = (() => { let c; const result = []; for (c of __py.iter(candidates)) { if (!__py.truth(__py.at(c, "valid"))) continue; result.push(c); } return result; })());
(pool = __py.or([() => (() => { let c; const result = []; for (c of __py.iter(valid)) { if (!__py.truth((__py.cmp("NotEq", __py.at(c, "variant"), previous)))) continue; result.push(c); } return result; })(), () => valid, () => candidates]));
return __py.max(pool, __py.kw({key: (c) => __py.at(c, "score")}));
}

// Fonte: src/slidedsl/layout_metrics.py

var OCCUPANCY_MINIMUM;
(OCCUPANCY_MINIMUM = 0.3);

function content_occupancy(...__args) {
var [slide] = __py.bind(__args, ["slide"], [undefined], false, false);
var clipped, e, r, region, relevant, titles, top;
(titles = (() => { let e; const result = []; for (e of __py.iter(slide.elements)) { if (!__py.truth((__py.cmp("Eq", e.role, "titulo")))) continue; result.push(e); } return result; })());
(top = __py.max((() => { let e; const result = []; for (e of __py.iter(titles)) { result.push(__py.bin("Add", __py.bin("Add", e.y, e.height), 16)); } return result; })(), __py.kw({default: 64})));
(region = [64, __py.min(top, 635), 1216, 636]);
(relevant = (() => { let e; const result = []; for (e of __py.iter(slide.elements)) { if (!__py.truth(__py.or([() => __py.and([() => (__py.cmp("Eq", e.type, "text")), () => (__py.cmp("NotEq", e.role, "titulo")), () => (__py.cmp("GtE", __py.or([() => e.font_size, () => 0]), 16))]), () => (__py.cmp("Eq", e.type, "image")), () => (__py.cmp("In", "_card_", e.id)), () => (__py.cmp("In", "_cabecalho_", e.id))]))) continue; result.push(e); } return result; })());
(clipped = (() => { let e, r; const result = []; for (e of __py.iter(relevant)) { if (!__py.truth((r = intersection(box(e), region)))) continue; result.push(r); } return result; })());
return __py.round(__py.bin("Div", union_area(clipped), area(region)), 4);
}

// Fonte: src/slidedsl/alto.py

var LIMITS;
(LIMITS = ({["topicos"]: ["items", 2, 5], ["etapas"]: ["items", 2, 5], ["conclusao"]: ["items", 2, 4], ["numeros"]: ["values", 1, 3], ["linha_do_tempo"]: ["milestones", 2, 6], ["grafico"]: ["bars", 2, 7], ["imagem"]: ["items", 0, 3]}));

var TEXT_LIMITS;
(TEXT_LIMITS = ({["title"]: 80, ["subtitle"]: 140, ["author"]: 80, ["text"]: 260, ["caption"]: 140, ["unit"]: 40, ["notes"]: 1500, ["label"]: 48, ["detail"]: 170, ["value"]: 14, ["date"]: 16, ["side"]: 40}));

function _num(v) { return String(v); }

var GENERIC;
(GENERIC = __py.re.compile("^(facilita|permite|melhora|ajuda|garante|aumenta|reduz|otimiza)\\b", __py.re.IGNORECASE));

function _digits(...__args) {
var [value] = __py.bind(__args, ["value"], [undefined], false, false);
return __py.re.sub("[^0-9]", "", value);
}

function number_tokens(...__args) {
var [text] = __py.bind(__args, ["text"], [undefined], false, false);
var found, match, raw, thousand, value;

(found = __py.set());
(text = __py.re.sub("\\bF\\d+\\b", " ", __py.or([() => text, () => ""])));
for (match of __py.iter(__py.re.finditer("\\d+(?:[.,]\\d+)*(\\s*mil\\b)?", text, __py.re.IGNORECASE))) {
(raw = __py.method(match, "group", 0));
(thousand = __py.bool(__py.method(match, "group", 1)));
(raw = __py.re.sub("\\s*mil$", "", raw, __py.kw({flags: __py.re.IGNORECASE})));
if (__py.truth(__py.re.fullmatch("\\d{1,3}([.,]\\d{3})+", raw))) {
(value = __py.re.sub("[.,]", "", raw));
} else {
(value = __py.method(raw, "replace", ",", "."));
}
(value = __py.method(value, "rstrip", "."));
if (__py.truth((__py.cmp("In", ".", value)))) {
(value = __py.method(__py.method(value, "rstrip", "0"), "rstrip", "."));
}
__py.method(found, "add", value);
if (__py.truth(thousand)) {
try {
__py.method(found, "add", __py.str(__py.int(__py.bin("Mult", __py.float(value), 1000))));
} catch (exception) {

}
}
}
return found;
}

function _norm(...__args) {
var [value] = __py.bind(__args, ["value"], [undefined], false, false);
return __py.method(__py.re.sub("[\\W_]+", " ", __py.method(__py.or([() => value, () => ""]), "casefold")), "strip");
}

function validate_alto(...__args) {
var [deck, facts] = __py.bind(__args, ["deck", "facts"], [undefined, null], false, false);
var attr, b, base, checks, cited, cited_numbers, count, detail, details, ds, entries, high, i, item, j, k, key, limit, low, m, n, name, number, numbers, path, quotes, r, ref, required, s, seen_items, side, texts, v, value;

(ds = []);
function emit(...__args) {
var [code, sev, msg, n, s, path, suggestion] = __py.bind(__args, ["code", "sev", "msg", "n", "s", "path", "suggestion"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined], false, false);
__py.method(ds, "append", Diagnostic(__py.kw({code: code, severity: sev, message: msg, slide: n, line: s.line, column: s.column, evidence: ({["path"]: path}), suggestion: suggestion})));
}
if (__py.truth(!__py.truth(deck.slides))) {
__py.method(ds, "append", Diagnostic(__py.kw({code: "A001", severity: "ERRO", message: "Deck sem slides."})));
}
for ([n, s] of __py.iter(__py.enumerate(deck.slides, 1))) {
(base = ("slides." + __py.format(__py.bin("Sub", n, 1), "", -1)));
(required = __py.method(({["citacao"]: ["text", "author"]}), "get", s.kind, ["title"]));
for (name of __py.iter(required)) {
if (__py.truth(!__py.truth(__py.method(__py.or([() => __py.getattr(s, name), () => ""]), "strip")))) {
emit("A002", "ERRO", ("Campo obrigatório vazio: " + __py.format(name, "", -1) + "."), n, s, (__py.format(base, "", -1) + "." + __py.format(name, "", -1)), "Preencha o campo com conteúdo específico do assunto.");
}
}
if (__py.truth((__py.cmp("In", s.kind, LIMITS)))) {
([attr, low, high] = __py.at(LIMITS, s.kind));
(count = __py.len(__py.getattr(s, attr)));
if (__py.truth(!__py.truth((__py.cmp("LtE", low, count) && __py.cmp("LtE", count, high))))) {
emit("A003", "ERRO", (__py.format(s.kind, "", -1) + " exige de " + __py.format(low, "", -1) + " a " + __py.format(high, "", -1) + " " + __py.format(attr, "", -1) + "; recebeu " + __py.format(count, "", -1) + "."), n, s, (__py.format(base, "", -1) + "." + __py.format(attr, "", -1)), ("Use entre " + __py.format(low, "", -1) + " e " + __py.format(high, "", -1) + " elementos."));
}
}
if (__py.truth((__py.cmp("Eq", s.kind, "comparacao")))) {
if (__py.truth((__py.cmp("NotEq", __py.len(s.sides), 2)))) {
emit("A003", "ERRO", "comparacao exige exatamente dois lados.", n, s, (__py.format(base, "", -1) + ".sides"), "Declare dois blocos lado.");
}
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
if (__py.truth(!__py.truth((__py.cmp("LtE", 1, __py.len(side.items)) && __py.cmp("LtE", __py.len(side.items), 4))))) {
emit("A003", "ERRO", "Cada lado da comparação exige 1–4 itens.", n, s, (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items"), "Use de 1 a 4 itens por lado.");
}
}
}
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
if (__py.truth(__py.re.fullmatch("\\W*(?:lado\\s*)?[a-z0-9]?\\W*", __py.method(__py.or([() => side.name, () => ""]), "casefold")))) {
emit("A024", "AVISO", "Nome do lado da comparação é genérico (letra ou vazio).", n, s, (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name"), "Nomeie o lado pela própria alternativa comparada.");
}
}
(entries = (() => { let i, k; const result = []; for ([k, i] of __py.iter(__py.enumerate(s.items))) { result.push([(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1)), i]); } return result; })());
entries = __py.bin("Add", entries, (() => { let i, j, k, side; const result = []; for ([k, side] of __py.iter(__py.enumerate(s.sides))) { for ([j, i] of __py.iter(__py.enumerate(side.items))) { result.push([(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1)), i]); }} return result; })());
(seen_items = __py.set());
for ([path, item] of __py.iter(entries)) {
(key = _norm((__py.format(item.label, "", -1) + " " + __py.format(__py.or([() => item.detail, () => ""]), "", -1))));
if (__py.truth(__py.and([() => key, () => (__py.cmp("In", key, seen_items))]))) {
emit("A023", "AVISO", "Item repetido no mesmo slide.", n, s, path, "Remova a repetição ou escreva um item com informação diferente.");
}
__py.method(seen_items, "add", key);
}
if (__py.truth(__py.and([() => (__py.cmp("Eq", s.kind, "imagem")), () => !__py.truth(__py.or([() => s.image_file, () => s.image_query]))]))) {
emit("A002", "ERRO", "imagem exige arquivo ou buscar.", n, s, (__py.format(base, "", -1) + ".image"), "Informe um arquivo local ou uma consulta de busca.");
}
if (__py.truth(__py.and([() => (__py.cmp("Eq", s.kind, "grafico")), () => __py.any((() => { let b; const result = []; for (b of __py.iter(s.bars)) { result.push((__py.cmp("Lt", b.value, 0))); } return result; })())]))) {
emit("A004", "ERRO", "Barras exigem valores não negativos.", n, s, (__py.format(base, "", -1) + ".bars"), "Use valores maiores ou iguais a zero.");
}
(checks = (() => { let k; const result = []; for (k of __py.iter(["title", "subtitle", "author", "text", "caption", "unit", "notes"])) { result.push([(__py.format(base, "", -1) + "." + __py.format(k, "", -1)), __py.getattr(s, k), __py.at(TEXT_LIMITS, k)]); } return result; })());
for ([k, i] of __py.iter(__py.enumerate(s.items))) {
checks = __py.bin("Add", checks, [[(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".label"), i.label, __py.at(TEXT_LIMITS, "label")], [(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".detail"), i.detail, __py.at(TEXT_LIMITS, "detail")]]);
}
for ([k, v] of __py.iter(__py.enumerate(s.values))) {
checks = __py.bin("Add", checks, [[(__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".value"), v.value, __py.at(TEXT_LIMITS, "value")], [(__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".label"), v.label, __py.at(TEXT_LIMITS, "detail")]]);
}
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
__py.method(checks, "append", [(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name"), side.name, __py.at(TEXT_LIMITS, "side")]);
for ([j, i] of __py.iter(__py.enumerate(side.items))) {
checks = __py.bin("Add", checks, [[(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1) + ".label"), i.label, __py.at(TEXT_LIMITS, "label")], [(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1) + ".detail"), i.detail, 80]]);
}
}
for ([k, m] of __py.iter(__py.enumerate(s.milestones))) {
checks = __py.bin("Add", checks, [[(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".date"), m.date, __py.at(TEXT_LIMITS, "date")], [(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".label"), m.label, 36], [(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".detail"), m.detail, 90]]);
}
for ([k, b] of __py.iter(__py.enumerate(s.bars))) {
__py.method(checks, "append", [(__py.format(base, "", -1) + ".bars." + __py.format(k, "", -1) + ".label"), b.label, 24]);
}
for ([path, value, limit] of __py.iter(checks)) {
if (__py.truth(__py.and([() => value, () => (__py.cmp("Gt", __py.len(value), limit))]))) {
emit("A005", "ERRO", ("Texto com " + __py.format(__py.len(value), "", -1) + " caracteres; limite " + __py.format(limit, "", -1) + "."), n, s, path, "Reescreva de forma mais concisa, mantendo o fato principal.");
}
}
if (__py.truth((__py.cmp("IsNot", facts, null)))) {
for (ref of __py.iter(s.sources)) {
if (__py.truth(__py.and([() => __py.re.fullmatch("F[0-9]+", ref), () => (__py.cmp("NotIn", ref, facts))]))) {
emit("A006", "ERRO", ("Fonte " + __py.format(ref, "", -1) + " não existe no dossiê de pesquisa."), n, s, (__py.format(base, "", -1) + ".sources"), "Cite somente IDs de fatos fornecidos.");
}
}
(cited = __py.method(" ", "join", (() => { let r; const result = []; for (r of __py.iter(s.sources)) { if (!__py.truth((__py.cmp("In", r, facts)))) continue; result.push(__py.bin("Add", __py.bin("Add", __py.method(__py.at(facts, r), "get", "quote", ""), " "), __py.method(__py.at(facts, r), "get", "claim", ""))); } return result; })()));
(numbers = __py.bin("Add", (() => { let v; const result = []; for (v of __py.iter(s.values)) { result.push(v.value); } return result; })(), (() => { let b; const result = []; for (b of __py.iter(s.bars)) { result.push(_num(b.value)); } return result; })()));
(cited_numbers = number_tokens(cited));
for (value of __py.iter(numbers)) {
if (__py.truth(__py.bin("Sub", number_tokens(value), cited_numbers))) {
emit("A007", "AVISO", ("Número " + __py.format(value, "", 114) + " não aparece nos fatos citados; pode ser inventado."), n, s, (__py.format(base, "", -1) + ".sources"), "Use números presentes nas fichas e cite o fato correspondente.");
}
}
(texts = [[(__py.format(base, "", -1) + ".title"), s.title], [(__py.format(base, "", -1) + ".subtitle"), s.subtitle]]);
texts = __py.bin("Add", texts, (() => { let key; const result = []; for (key of __py.iter(["caption", "text", "unit", "author"])) { result.push([(__py.format(base, "", -1) + "." + __py.format(key, "", -1)), __py.getattr(s, key)]); } return result; })());
texts = __py.bin("Add", texts, (() => { let i, k; const result = []; for ([k, i] of __py.iter(__py.enumerate(s.items))) { result.push([(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".detail"), i.detail]); } return result; })());
texts = __py.bin("Add", texts, (() => { let i, k; const result = []; for ([k, i] of __py.iter(__py.enumerate(s.items))) { result.push([(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".label"), i.label]); } return result; })());
texts = __py.bin("Add", texts, (() => { let i, j, k, side; const result = []; for ([k, side] of __py.iter(__py.enumerate(s.sides))) { for ([j, i] of __py.iter(__py.enumerate(side.items))) { result.push([(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1) + ".detail"), i.detail]); }} return result; })());
texts = __py.bin("Add", texts, (() => { let k, side; const result = []; for ([k, side] of __py.iter(__py.enumerate(s.sides))) { result.push([(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name"), side.name]); } return result; })());
texts = __py.bin("Add", texts, (() => { let item, j, k, side; const result = []; for ([k, side] of __py.iter(__py.enumerate(s.sides))) { for ([j, item] of __py.iter(__py.enumerate(side.items))) { result.push([(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1) + ".label"), item.label]); }} return result; })());
texts = __py.bin("Add", texts, (() => { let k, m; const result = []; for ([k, m] of __py.iter(__py.enumerate(s.milestones))) { result.push([(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".label"), m.label]); } return result; })());
texts = __py.bin("Add", texts, (() => { let b, k; const result = []; for ([k, b] of __py.iter(__py.enumerate(s.bars))) { result.push([(__py.format(base, "", -1) + ".bars." + __py.format(k, "", -1) + ".label"), b.label]); } return result; })());
texts = __py.bin("Add", texts, (() => { let k, m; const result = []; for ([k, m] of __py.iter(__py.enumerate(s.milestones))) { result.push([(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".date"), m.date]); } return result; })());
texts = __py.bin("Add", texts, (() => { let k, m; const result = []; for ([k, m] of __py.iter(__py.enumerate(s.milestones))) { result.push([(__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1) + ".detail"), m.detail]); } return result; })());
texts = __py.bin("Add", texts, (() => { let k, v; const result = []; for ([k, v] of __py.iter(__py.enumerate(s.values))) { result.push([(__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".label"), v.label]); } return result; })());
texts = __py.bin("Add", texts, [[(__py.format(base, "", -1) + ".notes"), s.notes]]);
for ([path, value] of __py.iter(texts)) {
for (number of __py.iter(__py.sorted(__py.bin("Sub", number_tokens(value), cited_numbers)))) {
if (__py.truth(number)) {
emit("A012", "AVISO", ("Número " + __py.format(number, "", 114) + " sem fato citado que o sustente."), n, s, path, "Remova o número ou cite o fato (Fn) em que ele aparece.");
break;
}
}
}
if (__py.truth(__py.and([() => (__py.cmp("Eq", s.kind, "citacao")), () => s.text]))) {
(quotes = __py.method(" ", "join", (() => { let r; const result = []; for (r of __py.iter(s.sources)) { if (!__py.truth((__py.cmp("In", r, facts)))) continue; result.push(__py.method(__py.at(facts, r), "get", "quote", "")); } return result; })()));
if (__py.truth(__py.or([() => __py.re.fullmatch("\\s*F\\d+\\s*", __py.or([() => s.author, () => ""])), () => !__py.truth(s.sources)]))) {
emit("A015", "ERRO", "Citação sem autor real (ID de fato não é autor).", n, s, (__py.format(base, "", -1) + ".author"), "Use o nome da pessoa ou documento citado.");
} else {
if (__py.truth((__py.cmp("NotIn", _norm(s.text), _norm(quotes))))) {
emit("A015", "ERRO", "Texto da citação não é cópia literal do fato citado.", n, s, (__py.format(base, "", -1) + ".text"), "Copie a frase exatamente como no trecho.");
}
}
}
if (__py.truth(__py.and([() => (__py.cmp("In", s.kind, ["numeros", "grafico", "citacao"])), () => !__py.truth(s.sources)]))) {
emit("A008", "AVISO", ("Slide " + __py.format(s.kind, "", -1) + " sem fonte."), n, s, (__py.format(base, "", -1) + ".sources"), "Cite o fato (F1, F2...) que sustenta os dados.");
}
}
(details = (() => { let i, k; const result = []; for ([k, i] of __py.iter(__py.enumerate(s.items))) { result.push([(__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".detail"), i.detail]); } return result; })());
details = __py.bin("Add", details, (() => { let i, j, k, side; const result = []; for ([k, side] of __py.iter(__py.enumerate(s.sides))) { for ([j, i] of __py.iter(__py.enumerate(side.items))) { result.push([(__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1) + ".detail"), i.detail]); }} return result; })());
for ([path, detail] of __py.iter(details)) {
if (__py.truth(__py.and([() => detail, () => __py.method(__py.slice(detail, null, 1, null), "islower")]))) {
emit("A009", "AVISO", "Detalhe não é uma frase completa (começa em minúscula, como um cenário solto).", n, s, path, "Escreva uma frase com sujeito e verbo que explique o rótulo.");
}
}
for ([k, i] of __py.iter(__py.enumerate(s.items))) {
if (__py.truth(__py.and([() => i.detail, () => (__py.cmp("Lt", __py.len(__py.method(i.detail, "split")), 4))]))) {
emit("A009", "AVISO", "Detalhe curto demais para explicar o item.", n, s, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".detail"), "Explique com um exemplo, número ou condição.");
} else {
if (__py.truth(__py.and([() => i.detail, () => __py.method(GENERIC, "match", i.detail), () => !__py.truth(__py.re.search("[0-9]", i.detail))]))) {
emit("A009", "AVISO", "Detalhe genérico (começa com verbo vago, sem dado).", n, s, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1) + ".detail"), "Troque por um fato, exemplo concreto ou número.");
}
}
}
}
return ds;
}

// Fonte: src/slidedsl/alto_layout.py

var W = WIDTH, H = HEIGHT, M = MARGIN;

var PALETTES;
(PALETTES = ({["claro"]: ({["bg"]: "#F6F8FC", ["text"]: "#14233D", ["muted"]: "#475569", ["primary"]: "#2563EB", ["on_primary"]: "#FFFFFF", ["soft"]: "#DDE8F9", ["card"]: "#FFFFFF", ["accent"]: "#B45309", ["on_accent"]: "#FFFFFF", ["line"]: "#CBD5E1"}), ["escuro"]: ({["bg"]: "#14233D", ["text"]: "#F1F5F9", ["muted"]: "#CBD5E1", ["primary"]: "#60A5FA", ["on_primary"]: "#14233D", ["soft"]: "#334765", ["card"]: "#1E3252", ["accent"]: "#FBBF24", ["on_accent"]: "#14233D", ["line"]: "#334765"})}));

function _palette(...__args) {
var [bg, text, muted, primary, soft, card, accent, line, on_primary, on_accent] = __py.bind(__args, ["bg", "text", "muted", "primary", "soft", "card", "accent", "line", "on_primary", "on_accent"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, "#FFFFFF", "#FFFFFF"], false, false);
return ({["bg"]: bg, ["text"]: text, ["muted"]: muted, ["primary"]: primary, ["on_primary"]: on_primary, ["soft"]: soft, ["card"]: card, ["accent"]: accent, ["on_accent"]: on_accent, ["line"]: line});
}

var _PALETTE_STYLES;
(_PALETTE_STYLES = ({["claro"]: [__py.at(PALETTES, "claro"), __py.at(PALETTES, "escuro"), "claro"], ["escuro"]: [__py.at(PALETTES, "escuro"), __py.at(PALETTES, "claro"), "escuro"], ["editorial"]: [_palette("#FAF7F2", "#1C1917", "#57534E", "#B4532A", "#EFE6DA", "#FFFFFF", "#1D4E89", "#D6CFC4"), _palette("#1C1917", "#FAF7F2", "#D6D3D1", "#F0A27A", "#3A3330", "#2A2522", "#9CC3F0", "#3A3330", __py.kw({on_primary: "#1C1917", on_accent: "#1C1917"})), "claro"], ["vibrante"]: [_palette("#FFFFFF", "#111827", "#4B5563", "#6D28D9", "#EDE9FE", "#F5F3FF", "#B45309", "#DDD6FE"), _palette("#4C1D95", "#FFFFFF", "#E9D5FF", "#FCD34D", "#5B21B6", "#5B21B6", "#FCD34D", "#6D28D9", __py.kw({on_primary: "#4C1D95", on_accent: "#4C1D95"})), "claro"], ["natural"]: [_palette("#F4F7F2", "#1F2A1F", "#4A5A4A", "#2F7A4F", "#DCEBDF", "#FFFFFF", "#B45309", "#C8D8CB"), _palette("#1F3D2B", "#F4F7F2", "#CFE3D4", "#9AE6B4", "#2C5440", "#2C5440", "#FBD38D", "#2C5440", __py.kw({on_primary: "#1F3D2B", on_accent: "#1F3D2B"})), "claro"], ["noturno"]: [_palette("#0F172A", "#E2E8F0", "#CBD5E1", "#38BDF8", "#1E293B", "#1E293B", "#F472B6", "#334155", __py.kw({on_primary: "#0F172A", on_accent: "#0F172A"})), _palette("#020617", "#F8FAFC", "#CBD5E1", "#38BDF8", "#0F172A", "#0F172A", "#F472B6", "#1E293B", __py.kw({on_primary: "#020617", on_accent: "#020617"})), "escuro"]}));

var STYLE_ATTRIBUTES;
(STYLE_ATTRIBUTES = ({["claro"]: ["Calibri", "Calibri", 0, "preenchido", "barra", "left", "lateral"], ["escuro"]: ["Calibri", "Calibri", 12, "preenchido", "ponto", "center", "base"], ["editorial"]: ["Georgia", "Calibri", 0, "fio", "numero", "left", "duplo"], ["vibrante"]: ["Trebuchet MS", "Calibri", 12, "preenchido", "numero", "center", "degraus"], ["natural"]: ["Cambria", "Calibri", 0, "bloco", "ponto", "left", "ramo"], ["noturno"]: ["Calibri", "Calibri", 0, "fio", "barra", "left", "canto", true]}));

var STYLES;
(STYLES = (() => { let name, palettes; const result = []; for ([name, palettes] of __py.iter(__py.method(_PALETTE_STYLES, "items"))) { result.push([name, new Estilo(...__py.iter(palettes), ...__py.iter(__py.at(STYLE_ATTRIBUTES, name)))]); } return Object.fromEntries(result); })());

var RENDER_BG;
(RENDER_BG = ({["claro"]: __py.at(__py.at(PALETTES, "claro"), "bg"), ["escuro"]: __py.at(__py.at(PALETTES, "escuro"), "bg")}));

var FEATURE_KINDS;
(FEATURE_KINDS = new Set(["capa", "conclusao"]));

function needed_height(...__args) {
var [text, width, size, bold, family] = __py.bind(__args, ["text", "width", "size", "bold", "family"], [undefined, undefined, undefined, false, "Arial"], false, false);
var capacity, cfg, estimate, line, lines, measured, px;

(cfg = load_rules());
(px = __py.bin("Div", __py.bin("Mult", size, 96), 72));
(capacity = __py.max(1, __py.math.floor(__py.bin("Div", __py.bin("Sub", width, __py.bin("Mult", 2, __py.at(cfg, "text_padding"))), __py.bin("Mult", __py.at(cfg, "character_width_factor"), px)))));
(lines = __py.sum((() => { let line; const result = []; for (line of __py.iter(__py.method(text, "split", "\n"))) { result.push(__py.max(1, __py.math.ceil(__py.bin("Div", __py.len(line), capacity)))); } return result; })()));
(estimate = __py.math.ceil(__py.bin("Add", __py.bin("Add", __py.bin("Mult", __py.bin("Mult", lines, px), __py.at(cfg, "line_height_factor")), __py.bin("Mult", 2, __py.at(cfg, "text_padding"))), 2)));

(measured = text_height(text, __py.bin("Mult", width, (__py.truth(bold) ? 0.95 : 0.98)), size, bold, family));
return (__py.truth((__py.cmp("Eq", family, "Arial"))) ? __py.max(estimate, measured) : measured);
}

class Builder {
constructor(...args) {
const values = __py.bind(args, ["number", "palette", "commands", "diagnostics", "mapping", "counter", "label_pt", "body_pt", "style", "variant", "root"], [undefined, undefined, [], [], {}, 0, LABEL_PT, BODY_PT, null, "", null]);
Object.assign(this, Object.fromEntries(["number", "palette", "commands", "diagnostics", "mapping", "counter", "label_pt", "body_pt", "style", "variant", "root"].map((n,i) => [n,values[i]])));
}
get title_pt() {
return optical_size(42, (__py.truth(this.style) ? this.style.fonte_titulo : "Arial"), MIN_TITLE_PT);
}
family(...__args) {
var [size, bold] = __py.bind(__args, ["size", "bold"], [undefined, false], false, false);
if (__py.truth(!__py.truth(this.style))) {
return "Arial";
}
return (__py.truth(__py.and([() => bold, () => (__py.cmp("GtE", size, MIN_TITLE_PT))])) ? this.style.fonte_titulo : this.style.fonte_corpo);
}
height(...__args) {
var [text, width, size, bold] = __py.bind(__args, ["text", "width", "size", "bold"], [undefined, undefined, undefined, false], false, false);
return needed_height(text, width, size, bold, __py.method(this, "family", size, bold));
}
card(...__args) {
var [x, y, w, h, accent] = __py.bind(__args, ["x", "y", "w", "h", "accent"], [undefined, undefined, undefined, undefined, false], false, false);
var p, style;
(p = this.palette);
(style = __py.or([() => this.style, () => __py.at(STYLES, "claro")]));
if (__py.truth((__py.cmp("Eq", style.cartao, "fio")))) {
__py.method(this, "rect", "card", x, y, w, RULE, __py.at(p, "primary"));
} else {
__py.method(this, "rect", "card", x, y, w, h, (__py.truth((__py.cmp("Eq", style.fonte_titulo, "Trebuchet MS"))) ? __py.at(p, "soft") : __py.at(p, "card")), __py.kw({rounded: __py.bool(style.raio)}));
if (__py.truth(__py.or([() => (__py.cmp("Eq", style.cartao, "bloco")), () => accent]))) {
__py.method(this, "rect", "faixa", x, y, XS, h, __py.at(p, "primary"));
}
}
}
marker(...__args) {
var [k, x, y] = __py.bind(__args, ["k", "x", "y"], [undefined, undefined, undefined], false, false);
var h, style;
(style = __py.or([() => this.style, () => __py.at(STYLES, "claro")]));
if (__py.truth((__py.cmp("Eq", style.marcador, "numero")))) {
(h = __py.method(this, "height", "00", XXL, this.label_pt, true));
__py.method(this, "text", "marcador", (__py.format(__py.bin("Add", k, 1), ("02d"), -1)), x, y, XXL, h, this.label_pt, __py.at(this.palette, "primary"), __py.kw({bold: true}));
} else {
if (__py.truth((__py.cmp("Eq", style.marcador, "ponto")))) {
__py.method(this, "ellipse", "marcador", x, __py.bin("Add", y, SM), XS, XS, __py.at(this.palette, "primary"));
} else {
__py.method(this, "rect", "marcador", x, __py.bin("Add", y, SM), XS, MD, __py.at(this.palette, "primary"));
}
}
}
_id(...__args) {
var [name] = __py.bind(__args, ["name"], [undefined], false, false);
this.counter = __py.bin("Add", this.counter, 1);
return ("s" + __py.format(this.number, "", -1) + "_" + __py.format(name, "", -1) + "_" + __py.format(this.counter, "", -1));
}
rect(...__args) {
var [name, x, y, w, h, color, role, rounded] = __py.bind(__args, ["name", "x", "y", "w", "h", "color", "role", "rounded"], [undefined, undefined, undefined, undefined, undefined, undefined, "decoracao", false], false, false);
var id;
(id = __py.method(this, "_id", name));
__py.method(this.commands, "append", Command(__py.kw({op: "add", id: id, element_type: "rectangle", position: Position(__py.kw({kind: "absolute", x: __py.round(x), y: __py.round(y)})), size: [__py.max(1, __py.round(w)), __py.max(1, __py.round(h))], color: color, role: role, rounded: rounded})));
return id;
}
ellipse(...__args) {
var [name, x, y, w, h, color, role] = __py.bind(__args, ["name", "x", "y", "w", "h", "color", "role"], [undefined, undefined, undefined, undefined, undefined, undefined, "decoracao"], false, false);
var id;
(id = __py.method(this, "_id", name));
__py.method(this.commands, "append", Command(__py.kw({op: "add", id: id, element_type: "ellipse", position: Position(__py.kw({kind: "absolute", x: __py.round(x), y: __py.round(y)})), size: [__py.round(w), __py.round(h)], color: color, role: role})));
return id;
}
image(...__args) {
var [name, file, x, y, w, h] = __py.bind(__args, ["name", "file", "x", "y", "w", "h"], [undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var id;
(id = __py.method(this, "_id", name));
__py.method(this.commands, "append", Command(__py.kw({op: "add", id: id, element_type: "image", file: file, position: Position(__py.kw({kind: "absolute", x: __py.round(x), y: __py.round(y)})), size: [__py.round(w), __py.round(h)], role: "nenhum"})));
return id;
}
fit(...__args) {
var [text, w, max_h, sizes, bold, path] = __py.bind(__args, ["text", "w", "max_h", "sizes", "bold", "path"], [undefined, undefined, undefined, undefined, false, null], false, false);
var h, size;
for (size of __py.iter(sizes)) {
(h = __py.method(this, "height", text, w, size, bold));
if (__py.truth((__py.cmp("LtE", h, __py.round(max_h))))) {
return [size, h];
}
}
(size = __py.at(sizes, -(1)));
(h = __py.method(this, "height", text, w, size, bold));
__py.method(this.diagnostics, "append", Diagnostic(__py.kw({code: "A010", severity: "ERRO", message: ("Texto não cabe no espaço do layout nem com " + __py.format(size, "", -1) + " pt."), slide: this.number, evidence: ({["path"]: path, ["needed"]: h, ["available"]: max_h}), suggestion: "Encurte este campo ou divida o conteúdo em dois slides."})));
return [size, h];
}
text(...__args) {
var [name, value, x, y, w, h, size, color, bold, align, role, path] = __py.bind(__args, ["name", "value", "x", "y", "w", "h", "size", "color", "bold", "align", "role", "path"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, false, "left", "nenhum", null], false, false);
var id, minimum;
(minimum = (__py.truth((__py.cmp("Eq", role, "titulo"))) ? MIN_TITLE_PT : (__py.truth(__py.and([() => path, () => __py.method(path, "endswith", ".subtitle")])) ? MIN_SUBTITLE_PT : (__py.truth(__py.and([() => path, () => __py.method(path, "endswith", [".label", ".name", ".date"])])) ? MIN_LABEL_PT : (__py.truth(__py.and([() => path, () => __py.method(path, "endswith", [".detail", ".text", ".unit"])])) ? MIN_BODY_PT : 0)))));
if (__py.truth((__py.cmp("Lt", size, minimum)))) {
__py.method(this.diagnostics, "append", Diagnostic(__py.kw({code: "A019", severity: "ERRO", slide: this.number, message: "Fonte abaixo do mínimo do papel.", evidence: ({["path"]: path, ["actual"]: size, ["minimum"]: minimum}), suggestion: "Mude a composição ou encurte o texto; não reduza a fonte."})));
}
(id = __py.method(this, "_id", name));
__py.method(this.commands, "append", Command(__py.kw({op: "add", id: id, element_type: "text", text: value, position: Position(__py.kw({kind: "absolute", x: __py.round(x), y: __py.round(y)})), size: [__py.round(w), __py.max(1, __py.round(h))], font_size: size, color: color, role: role, font_face: __py.method(this, "family", size, bold), bold: bold, align: align})));
if (__py.truth(path)) {
(this.mapping[id] = path);
}
return id;
}
fitted(...__args) {
var [name, value, x, y, w, max_h, sizes, color, path, kw] = __py.bind(__args, ["name", "value", "x", "y", "w", "max_h", "sizes", "color", "path"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined], false, true);
var h, size;
([size, h] = __py.method(this, "fit", value, w, max_h, sizes, __py.method(kw, "get", "bold", false), path));
__py.method(this, "text", name, value, x, y, w, h, size, color, __py.kw({path: path, ...kw}));
return h;
}
notes(...__args) {
var [value] = __py.bind(__args, ["value"], [undefined], false, false);
if (__py.truth(value)) {
__py.method(this.commands, "append", Command(__py.kw({op: "notes", text: value})));
}
}
}

function source_label(...__args) {
var [ref, facts] = __py.bind(__args, ["ref", "facts"], [undefined, undefined], false, false);
var fact, host, title;
(fact = __py.method(facts, "get", ref));
if (__py.truth(fact)) {
(title = __py.or([() => __py.method(fact, "get", "source_title"), () => ""]));
(host = __py.or([() => __py.urlsplit(__py.or([() => __py.method(fact, "get", "url"), () => ""])).hostname, () => ""]));
(host = __py.re.sub("^www\\.", "", host));
return (__py.truth(__py.and([() => title, () => host])) ? (__py.format(title, "", -1) + " (" + __py.format(host, "", -1) + ")") : __py.or([() => title, () => host, () => ref]));
}
return ref;
}

function header(...__args) {
var [b, s, base] = __py.bind(__args, ["b", "s", "base"], [undefined, undefined, undefined], false, false);
var h, p, size, title, width;
(p = b.palette);
(width = (__py.truth(__py.and([() => (__py.cmp("Eq", s.kind, "imagem")), () => (__py.cmp("Eq", b.variant, "photo50"))])) ? __py.at(col(0, 6), 1) : __py.at(col(0, 12), 1)));
(title = balanced_title(s.title, width, b.title_pt, __py.kw({family: __py.method(b, "family", b.title_pt, true)})));
__py.method(b, "rect", "marca", M, __py.bin("Sub", TITLE_Y, SM), XL, RULE, __py.at(p, "primary"));
if (__py.truth(b.style.margem_vertical)) {
__py.method(b, "rect", "margem", MD, TITLE_Y, RULE, __py.bin("Sub", CONTENT_BOTTOM, TITLE_Y), __py.at(p, "primary"));
}
([size, h] = __py.method(b, "fit", title, width, __py.bin("Mult", XXL, 4), [b.title_pt], true, (__py.format(base, "", -1) + ".title")));
__py.method(b, "text", "titulo", title, M, TITLE_Y, width, h, size, __py.at(p, "text"), __py.kw({bold: true, align: "left", role: "titulo", path: (__py.format(base, "", -1) + ".title")}));
return __py.bin("Add", __py.bin("Add", TITLE_Y, h), SM);
}

var LABELED_REF;
(LABELED_REF = __py.re.compile("^[A-ZÀ-Ý][\\wÀ-ÿ ]{1,24}:\\s"));

function footer(...__args) {
var [b, s, facts, total] = __py.bind(__args, ["b", "s", "facts", "total"], [undefined, undefined, undefined, undefined], false, false);
var extra, fact, label, labels, p, prefix, ref, shown, value, x;

(p = b.palette);
(labels = []);
for (ref of __py.iter(s.sources)) {
(fact = __py.method(facts, "get", ref));
if (__py.truth(__py.and([() => fact, () => __py.method(__py.or([() => __py.method(fact, "get", "url"), () => ""]), "startswith", "documento:")]))) {
(label = __py.or([() => __py.method(fact, "get", "source_title"), () => ref]));
} else {
if (__py.truth(fact)) {
(label = __py.or([() => __py.re.sub("^www\\.", "", __py.or([() => __py.urlsplit(__py.or([() => __py.method(fact, "get", "url"), () => ""])).hostname, () => ""])), () => ref]));
} else {
(label = ref);
}
}
if (__py.truth((__py.cmp("NotIn", label, labels)))) {
__py.method(labels, "append", label);
}
}
if (__py.truth(labels)) {
(shown = __py.list(labels));
while (__py.truth(true)) {
(extra = __py.bin("Sub", __py.len(labels), __py.len(shown)));
(prefix = (__py.truth(__py.all((() => { let x; const result = []; for (x of __py.iter(shown)) { result.push(__py.method(LABELED_REF, "match", x)); } return result; })())) ? "" : "Fonte: "));
(value = __py.bin("Add", __py.bin("Add", prefix, __py.method("; ", "join", shown)), (__py.truth(extra) ? (" e mais " + __py.format(extra, "", -1)) : "")));
if (__py.truth(__py.or([() => (__py.cmp("LtE", __py.method(b, "height", value, 1000, 12), 40)), () => (__py.cmp("Eq", __py.len(shown), 1))]))) {
break;
}
__py.method(shown, "pop");
}
if (__py.truth((__py.cmp("Gt", __py.method(b, "height", value, 1000, 12), 40)))) {
(value = __py.bin("Add", __py.at(__py.method(__py.slice(value, null, 100, null), "rsplit", " ", 1), 0), "…"));
}
__py.method(b, "text", "fonte", value, M, 664, 1000, 40, 12, __py.at(p, "muted"), __py.kw({path: ("slides." + __py.format(__py.bin("Sub", b.number, 1), "", -1) + ".sources")}));
}
__py.method(b, "text", "pagina", (__py.format(b.number, "", -1) + "/" + __py.format(total, "", -1)), __py.bin("Sub", __py.bin("Sub", W, M), 120), 664, 120, 40, 12, __py.at(p, "muted"), __py.kw({align: "right"}));
}

function uniform(...__args) {
var [b, entries, w, max_h, sizes, bold] = __py.bind(__args, ["b", "entries", "w", "max_h", "sizes", "bold"], [undefined, undefined, undefined, undefined, undefined, false], false, false);
var _, heights, path, size, t;

(entries = (() => { let path, t; const result = []; for ([t, path] of __py.iter(entries)) { if (!__py.truth(t)) continue; result.push([t, path]); } return result; })());
if (__py.truth(__py.and([() => entries, () => __py.all((() => { let _, path; const result = []; for ([_, path] of __py.iter(entries)) { result.push(__py.method(path, "endswith", [".label", ".detail", ".subtitle"])); } return result; })())]))) {
(sizes = [(__py.truth(bold) ? b.label_pt : b.body_pt)]);
}
if (__py.truth(!__py.truth(entries))) {
return [__py.at(sizes, 0), 0];
}
for (size of __py.iter(sizes)) {
(heights = (() => { let _, t; const result = []; for ([t, _] of __py.iter(entries)) { result.push(__py.method(b, "height", t, w, size, bold)); } return result; })());
if (__py.truth((__py.cmp("LtE", __py.max(heights), max_h)))) {
return [size, __py.max(heights)];
}
}
(size = __py.at(sizes, -(1)));
for ([t, path] of __py.iter(entries)) {
__py.method(b, "fit", t, w, max_h, [size], bold, path);
}
return [size, __py.max((() => { let _, t; const result = []; for ([t, _] of __py.iter(entries)) { result.push(__py.method(b, "height", t, w, size, bold)); } return result; })())];
}

function label_detail_sizes(...__args) {
var [b, labels, details, w, label_max, block_h, label_sizes, detail_sizes] = __py.bind(__args, ["b", "labels", "details", "w", "label_max", "block_h", "label_sizes", "detail_sizes"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var best, dh, ds, ds_, lh, ls, ls_, probe;

(probe = new Builder(b.number, b.palette, __py.kw({style: b.style})));
(best = null);
for (ls of __py.iter(label_sizes)) {
([ls_, lh] = uniform(probe, labels, w, label_max, [ls], true));
if (__py.truth(probe.diagnostics)) {
__py.method(probe.diagnostics, "clear");
continue;
}
for (ds of __py.iter(detail_sizes)) {
([ds_, dh] = uniform(probe, details, w, __py.bin("Sub", block_h, lh), [ds]));
if (__py.truth(!__py.truth(probe.diagnostics))) {
if (__py.truth(__py.or([() => (__py.cmp("Is", best, null)), () => (__py.cmp("Gt", ds, __py.at(best, 2))), () => __py.and([() => (__py.cmp("Eq", ds, __py.at(best, 2))), () => (__py.cmp("Gt", ls, __py.at(best, 0)))])]))) {
(best = [ls, lh, ds, dh]);
}
break;
}
__py.method(probe.diagnostics, "clear");
}
}
if (__py.truth(best)) {
return best;
}
([ls, lh] = uniform(b, labels, w, label_max, __py.slice(label_sizes, -(1), null, null), true));
([ds, dh] = uniform(b, details, w, __py.bin("Sub", block_h, lh), __py.slice(detail_sizes, -(1), null, null)));
return [ls, lh, ds, dh];
}

function layout_capa(...__args) {
var [b, s, base, deck] = __py.bind(__args, ["b", "s", "base", "deck"], [undefined, undefined, undefined, undefined], false, false);
var ah, align, has_photo, k, motif, p, sh, ss, th, title, total, w, y;
(p = b.palette);
(has_photo = (__py.truth(s.image_file) ? photo(b, s, base) : false));
if (__py.truth(!__py.truth(has_photo))) {
(motif = b.style.motivo_capa);
if (__py.truth((__py.cmp("Eq", motif, "lateral")))) {
__py.method(b, "rect", "faixa", 0, 0, SM, H, __py.at(p, "primary"));
} else {
if (__py.truth((__py.cmp("Eq", motif, "base")))) {
__py.method(b, "rect", "faixa", 0, __py.bin("Sub", H, LG), W, LG, __py.at(p, "primary"));
} else {
if (__py.truth((__py.cmp("Eq", motif, "duplo")))) {
__py.method(b, "rect", "faixa", M, XXL, __py.at(col(0, 12), 1), RULE, __py.at(p, "primary"));
__py.method(b, "rect", "faixa", M, __py.bin("Sub", H, XXL), __py.at(col(0, 12), 1), RULE, __py.at(p, "primary"));
} else {
if (__py.truth((__py.cmp("Eq", motif, "degraus")))) {
for (k of __py.iter(__py.range(3))) {
__py.method(b, "rect", "faixa", __py.bin("Sub", W, __py.bin("Mult", XXL, __py.bin("Add", k, 1))), __py.bin("Sub", H, __py.bin("Mult", LG, __py.bin("Add", k, 1))), XXL, LG, __py.at(p, "primary"));
}
} else {
if (__py.truth((__py.cmp("Eq", motif, "ramo")))) {
__py.method(b, "rect", "faixa", M, __py.bin("Sub", H, XXL), __py.at(col(0, 4), 1), XS, __py.at(p, "primary"));
} else {
__py.method(b, "rect", "faixa", __py.bin("Sub", W, LG), 0, LG, __py.bin("Mult", XXL, 3), __py.at(p, "primary"));
}
}
}
}
}
}
(w = (__py.truth(has_photo) ? __py.at(col(0, 6), 1) : __py.at(col(0, 10), 1)));
(align = b.style.alinhamento_titulo);
(title = balanced_title(sentence_case(s.title), w, b.title_pt, __py.kw({family: __py.method(b, "family", b.title_pt, true)})));
(th = __py.method(b, "height", title, w, b.title_pt, true));
if (__py.truth((__py.cmp("Gt", th, 320)))) {
__py.method(b, "fit", s.title, w, 320, [b.title_pt], true, (__py.format(base, "", -1) + ".title"));
}
([ss, sh] = uniform(b, [[s.subtitle, (__py.format(base, "", -1) + ".subtitle")]], w, 180, [24]));
(ah = (__py.truth(s.author) ? __py.method(b, "height", s.author, w, 18) : 0));
(total = __py.bin("Add", __py.bin("Add", th, (__py.truth(s.subtitle) ? __py.bin("Add", sh, 12) : 0)), (__py.truth(s.author) ? __py.bin("Add", ah, 20) : 0)));
(y = __py.max(120, __py.bin("Div", __py.bin("Sub", H, total), 2)));
__py.method(b, "rect", "marca", (__py.truth((__py.cmp("Eq", align, "center"))) ? __py.bin("Add", M, __py.bin("Div", __py.bin("Sub", w, 72), 2)) : M), __py.bin("Sub", y, 28), 72, 8, __py.at(p, "primary"));
__py.method(b, "text", "titulo", title, M, y, w, th, b.title_pt, __py.at(p, "text"), __py.kw({bold: true, role: "titulo", path: (__py.format(base, "", -1) + ".title"), align: b.style.alinhamento_titulo}));
y = __py.bin("Add", y, __py.bin("Add", th, 12));
if (__py.truth(s.subtitle)) {
__py.method(b, "text", "subtitulo", s.subtitle, M, y, w, sh, ss, __py.at(p, "muted"), __py.kw({align: align, path: (__py.format(base, "", -1) + ".subtitle")}));
y = __py.bin("Add", y, __py.bin("Add", sh, 20));
}
if (__py.truth(s.author)) {
__py.method(b, "text", "autor", s.author, M, y, w, ah, 18, __py.at(p, "primary"), __py.kw({bold: true, align: align, path: (__py.format(base, "", -1) + ".author")}));
}
}

function layout_secao(...__args) {
var [b, s, base, deck] = __py.bind(__args, ["b", "s", "base", "deck"], [undefined, undefined, undefined, undefined], false, false);
var align, index, k, motif, p, sh, size, ss, th, title, w, x, y;
if (__py.truth((__py.cmp("Lt", __py.len(deck.slides), 8)))) {
([p, motif] = [b.palette, b.style.motivo_capa]);
if (__py.truth((__py.cmp("In", motif, new Set(["base", "ramo"]))))) {
__py.method(b, "rect", "transicao_bloco", 0, __py.bin("Div", __py.bin("Mult", H, 2), 3), W, __py.bin("Div", H, 3), __py.at(p, "soft"));
__py.method(b, "rect", "faixa", M, __py.bin("Div", __py.bin("Mult", H, 2), 3), __py.at(col(0, 4), 1), XS, __py.at(p, "primary"));
} else {
__py.method(b, "rect", "transicao_bloco", __py.bin("Div", __py.bin("Mult", W, 2), 3), 0, __py.bin("Div", W, 3), H, __py.at(p, "soft"));
if (__py.truth((__py.cmp("Eq", motif, "degraus")))) {
for (k of __py.iter(__py.range(3))) {
__py.method(b, "rect", "faixa", __py.bin("Add", __py.bin("Div", __py.bin("Mult", W, 2), 3), __py.bin("Mult", k, XXL)), __py.bin("Sub", H, __py.bin("Mult", LG, __py.bin("Add", k, 1))), XXL, LG, __py.at(p, "primary"));
}
} else {
if (__py.truth((__py.cmp("Eq", motif, "duplo")))) {
for (y of __py.iter([XXL, __py.bin("Sub", H, XXL)])) {
__py.method(b, "rect", "faixa", __py.bin("Div", __py.bin("Mult", W, 2), 3), y, __py.bin("Div", W, 3), RULE, __py.at(p, "primary"));
}
} else {
__py.method(b, "rect", "faixa", __py.bin("Div", __py.bin("Mult", W, 2), 3), 0, XS, H, __py.at(p, "primary"));
}
}
}
(w = __py.at(col(0, 8), 1));
(size = __py.min(54, optical_size(48, b.style.fonte_titulo, MIN_TITLE_PT)));
(title = balanced_title(s.title, w, size, __py.kw({family: __py.method(b, "family", size, true)})));
(th = __py.method(b, "height", title, w, size, true));
(sh = (__py.truth(s.subtitle) ? __py.method(b, "height", s.subtitle, w, b.body_pt) : 0));
(y = __py.bin("Div", __py.bin("Sub", __py.bin("Sub", __py.bin("Sub", __py.bin("Mult", H, (__py.truth((__py.cmp("In", motif, new Set(["base", "ramo"])))) ? __py.bin("Div", 2, 3) : 1)), th), sh), LABEL_GAP), 2));
(align = b.style.alinhamento_titulo);
__py.method(b, "rect", "marca", (__py.truth((__py.cmp("Eq", align, "center"))) ? __py.bin("Add", M, __py.bin("Div", __py.bin("Sub", w, XL), 2)) : M), __py.bin("Sub", y, LG), XL, RULE, __py.at(p, "primary"));
__py.method(b, "text", "transicao", title, M, y, w, th, size, __py.at(p, "text"), __py.kw({bold: true, align: align, role: "titulo", path: __py.bin("Add", base, ".title")}));
if (__py.truth(s.subtitle)) {
__py.method(b, "text", "subtitulo", s.subtitle, M, __py.bin("Add", __py.bin("Add", y, th), LABEL_GAP), w, sh, b.body_pt, __py.at(p, "muted"), __py.kw({align: align, path: __py.bin("Add", base, ".subtitle")}));
}
return null;
}
(p = b.palette);
__py.method(b, "rect", "painel", 0, 0, 420, H, __py.at(p, "primary"));
(index = __py.sum((() => { let x; const result = []; for (x of __py.iter(__py.slice(deck.slides, null, b.number, null))) { if (!__py.truth((__py.cmp("Eq", x.kind, "secao")))) continue; result.push(1); } return result; })()));
__py.method(b, "text", "numero", (__py.format(index, ("02d"), -1)), 64, 270, 300, __py.method(b, "height", "00", 300, 96, true), 96, __py.at(p, "on_primary"), __py.kw({bold: true}));
(th = __py.method(b, "height", s.title, 732, b.title_pt, true));
([ss, sh] = uniform(b, [[s.subtitle, (__py.format(base, "", -1) + ".subtitle")]], 732, 180, [26, 24, 22, 20]));
(y = __py.bin("Div", __py.bin("Sub", __py.bin("Sub", H, th), (__py.truth(s.subtitle) ? __py.bin("Add", sh, 12) : 0)), 2));
__py.method(b, "text", "titulo", s.title, 484, y, 732, th, b.title_pt, __py.at(p, "text"), __py.kw({bold: true, role: "titulo", path: (__py.format(base, "", -1) + ".title"), align: b.style.alinhamento_titulo}));
if (__py.truth(s.subtitle)) {
__py.method(b, "text", "subtitulo", s.subtitle, 484, __py.bin("Add", __py.bin("Add", y, th), 12), 732, sh, ss, __py.at(p, "muted"), __py.kw({align: b.style.alinhamento_titulo, path: (__py.format(base, "", -1) + ".subtitle")}));
}
}

function editorial_items(...__args) {
var [b, items, base, x, top, w, bottom, headings, cards] = __py.bind(__args, ["b", "items", "base", "x", "top", "w", "bottom", "headings", "cards"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, [], false], false, false);
var ch, columns, cw, cx, cy, detail_w, detail_x, dh, free, gap, h, height, heights, i, inner, item, k, lab, label, label_w, labels, lh, marker_w, natural, p, rows, y;

if (__py.truth(!__py.truth(items))) {
return null;
}
(p = b.palette);
(labels = visible_labels(items, ...__py.iter(headings)));
if (__py.truth(cards)) {
(columns = (__py.truth((__py.cmp("Eq", b.variant, "grid"))) ? 2 : __py.len(items)));
(rows = __py.math.ceil(__py.bin("Div", __py.len(items), columns)));
(cw = __py.bin("Div", __py.bin("Sub", w, __py.bin("Mult", MD, __py.bin("Sub", columns, 1))), columns));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, CARD_PADDING)));
(lh = __py.max((() => { let lab; const result = []; for (lab of __py.iter(labels)) { result.push((__py.truth(lab) ? __py.method(b, "height", lab, inner, b.label_pt, true) : 0)); } return result; })(), __py.kw({default: 0})));
(dh = __py.max((() => { let i; const result = []; for (i of __py.iter(items)) { result.push((__py.truth(i.detail) ? __py.method(b, "height", i.detail, inner, b.body_pt) : 0)); } return result; })(), __py.kw({default: 0})));
(natural = __py.bin("Add", __py.bin("Mult", rows, __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Mult", 2, CARD_PADDING), lh), LABEL_GAP), dh)), __py.bin("Mult", MD, __py.bin("Sub", rows, 1))));
(y = card_position(top, natural, bottom));
check_block_bottom(b, y, natural, bottom, base);
(ch = __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Mult", 2, CARD_PADDING), lh), LABEL_GAP), dh));
for ([k, [item, label]] of __py.iter(__py.enumerate(__py.zip(items, labels)))) {
(cx = __py.bin("Add", x, __py.bin("Mult", __py.bin("Mod", k, columns), __py.bin("Add", cw, MD))));
(cy = __py.bin("Add", y, __py.bin("Mult", __py.bin("FloorDiv", k, columns), __py.bin("Add", ch, MD))));
__py.method(b, "card", cx, cy, cw, ch);
draw_item(b, item, label, (__py.format(base, "", -1) + "." + __py.format(k, "", -1)), __py.bin("Add", cx, CARD_PADDING), __py.bin("Add", cy, CARD_PADDING), inner, __py.bin("Sub", ch, __py.bin("Mult", 2, CARD_PADDING)), lh, dh);
}
return null;
}
(marker_w = (__py.truth((__py.cmp("Eq", b.style.marcador, "numero"))) ? XXL : MD));
(label_w = __py.bin("Mult", w, 0.32));
(detail_x = __py.bin("Add", __py.bin("Add", __py.bin("Add", x, marker_w), label_w), MD));
(detail_w = __py.bin("Sub", __py.bin("Sub", __py.bin("Sub", w, marker_w), label_w), MD));
(heights = (() => { let i, lab; const result = []; for ([i, lab] of __py.iter(__py.zip(items, labels))) { result.push(__py.max((__py.truth(lab) ? __py.method(b, "height", lab, label_w, b.label_pt, true) : 0), (__py.truth(i.detail) ? __py.method(b, "height", i.detail, detail_w, b.body_pt) : 0))); } return result; })());
(free = __py.bin("Sub", __py.bin("Sub", bottom, top), __py.sum(heights)));
(gap = __py.min(XXL, __py.max(XS, __py.bin("Div", free, __py.max(1, __py.bin("Sub", __py.len(items), 1))))));
(height = __py.bin("Add", __py.sum(heights), __py.bin("Mult", gap, __py.bin("Sub", __py.len(items), 1))));
(y = __py.bin("Add", top, __py.min(XL, __py.bin("Mult", __py.max(0, __py.bin("Sub", __py.bin("Sub", bottom, top), height)), 0.44))));
for ([k, [item, label, h]] of __py.iter(__py.enumerate(__py.zip(items, labels, heights)))) {
__py.method(b, "marker", k, x, y);
if (__py.truth(label)) {
__py.method(b, "fitted", "rotulo", label, __py.bin("Add", x, marker_w), y, label_w, __py.bin("Sub", bottom, y), [b.label_pt], __py.at(p, "text"), __py.kw({bold: true, path: (__py.format(base, "", -1) + "." + __py.format(k, "", -1) + ".label")}));
}
if (__py.truth(item.detail)) {
__py.method(b, "fitted", "detalhe", item.detail, detail_x, y, detail_w, __py.bin("Sub", bottom, y), [b.body_pt], __py.at(p, "muted"), __py.kw({role: "corpo", path: (__py.format(base, "", -1) + "." + __py.format(k, "", -1) + ".detail")}));
}
y = __py.bin("Add", y, __py.bin("Add", h, gap));
}
}

function check_block_bottom(...__args) {
var [b, y, height, bottom, path] = __py.bind(__args, ["b", "y", "height", "bottom", "path"], [undefined, undefined, undefined, undefined, undefined], false, false);

if (__py.truth((__py.cmp("Gt", __py.bin("Add", y, height), __py.bin("Add", bottom, 0.5))))) {
__py.method(b.diagnostics, "append", Diagnostic(__py.kw({code: "A010", severity: "ERRO", slide: b.number, message: "Bloco de cartões ultrapassa o limite inferior da área de conteúdo.", evidence: ({["path"]: path, ["bottom"]: __py.bin("Add", y, height), ["limit"]: bottom})})));
}
}

function draw_item(...__args) {
var [b, item, label, path, x, y, w, available, lh, dh] = __py.bind(__args, ["b", "item", "label", "path", "x", "y", "w", "available", "lh", "dh"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var gap;
(gap = (__py.truth(__py.and([() => label, () => item.detail])) ? LABEL_GAP : 0));
if (__py.truth((__py.cmp("Gt", __py.bin("Add", __py.bin("Add", lh, dh), gap), available)))) {
__py.method(b.diagnostics, "append", Diagnostic(__py.kw({code: "A010", severity: "ERRO", slide: b.number, message: "Conteúdo excede o cartão na fonte do papel.", evidence: ({["path"]: path, ["needed"]: __py.bin("Add", __py.bin("Add", lh, dh), gap), ["available"]: available})})));
}
if (__py.truth(label)) {
__py.method(b, "text", "rotulo", label, x, y, w, lh, b.label_pt, __py.at(b.palette, "text"), __py.kw({bold: true, path: __py.bin("Add", path, ".label")}));
}
if (__py.truth(item.detail)) {
__py.method(b, "text", "detalhe", item.detail, x, __py.bin("Add", __py.bin("Add", y, lh), gap), w, dh, b.body_pt, __py.at(b.palette, "muted"), __py.kw({role: "corpo", path: __py.bin("Add", path, ".detail")}));
}
}

function layout_topicos(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var w, x;
([x, w] = col(0, 12));
editorial_items(b, s.items, __py.bin("Add", base, ".items"), x, top, w, CONTENT_BOTTOM, [s.title], __py.kw({cards: (__py.cmp("In", b.variant, new Set(["cards", "grid"])))}));
}

function layout_numeros(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var cw, cx, height, inner, k, lh, ls, n, natural, p, rh, v, vh, vs, w, x, y;
([p, n] = [b.palette, __py.len(s.values)]);
([x, w] = col(0, 12));
if (__py.truth((__py.cmp("Eq", b.variant, "number_rows")))) {
(natural = __py.sum((() => { let v; const result = []; for (v of __py.iter(s.values)) { result.push(__py.max(__py.method(b, "height", v.value, __py.at(col(0, 4), 1), 64, true), __py.method(b, "height", v.label, __py.at(col(4, 8), 1), b.label_pt))); } return result; })()));
([y, height] = distribute(top, __py.bin("Add", natural, __py.bin("Mult", MD, __py.bin("Sub", n, 1))), n));
(rh = __py.bin("Div", __py.bin("Sub", height, __py.bin("Mult", MD, __py.bin("Sub", n, 1))), n));
for ([k, v] of __py.iter(__py.enumerate(s.values))) {
__py.method(b, "card", x, y, w, rh);
__py.method(b, "fitted", "valor", v.value, __py.bin("Add", x, LG), __py.bin("Add", y, XS), __py.bin("Sub", __py.at(col(0, 4), 1), LG), __py.bin("Sub", rh, SM), [64, 56, 48], __py.at(p, "primary"), __py.kw({bold: true, path: (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".value")}));
__py.method(b, "fitted", "legenda", v.label, __py.at(col(4, 8), 0), __py.bin("Add", y, SM), __py.bin("Sub", __py.at(col(4, 8), 1), LG), __py.bin("Sub", rh, LG), [b.label_pt], __py.at(p, "text"), __py.kw({path: (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".label")}));
y = __py.bin("Add", y, __py.bin("Add", rh, MD));
}
return null;
}
(cw = __py.bin("Div", __py.bin("Sub", w, __py.bin("Mult", MD, __py.bin("Sub", n, 1))), n));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, LG)));
([vs, vh] = uniform(b, (() => { let k, v; const result = []; for ([k, v] of __py.iter(__py.enumerate(s.values))) { result.push([v.value, (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".value")]); } return result; })(), inner, __py.bin("Mult", XXL, 3), [88, 80, 72, 64, 56, 48], true));
([ls, lh] = uniform(b, (() => { let k, v; const result = []; for ([k, v] of __py.iter(__py.enumerate(s.values))) { result.push([v.label, (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".label")]); } return result; })(), inner, __py.bin("Mult", XXL, 3), [b.label_pt]));
([y, height] = distribute(top, __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Mult", 2, LG), vh), MD), lh), __py.max(2, n)));
for ([k, v] of __py.iter(__py.enumerate(s.values))) {
(cx = __py.bin("Add", x, __py.bin("Mult", k, __py.bin("Add", cw, MD))));
__py.method(b, "card", cx, y, cw, height);
__py.method(b, "text", "valor", v.value, __py.bin("Add", cx, LG), __py.bin("Add", y, LG), inner, vh, vs, __py.at(p, "primary"), __py.kw({bold: true, path: (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".value")}));
__py.method(b, "fitted", "legenda", v.label, __py.bin("Add", cx, LG), __py.bin("Add", __py.bin("Add", __py.bin("Add", y, LG), vh), MD), inner, __py.bin("Sub", __py.bin("Sub", __py.bin("Sub", height, __py.bin("Mult", 2, LG)), vh), MD), [ls], __py.at(p, "text"), __py.kw({path: (__py.format(base, "", -1) + ".values." + __py.format(k, "", -1) + ".label")}));
}
}

function comparison_columns(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var _, all_items, body_top, count, cw, cy, dw, gap, height, heights, inner, item, j, k, longest, lw, minimum_lw, natural, nh, options, p, path, side, step, word, x, y;
(p = b.palette);
([_, cw] = col(0, 6));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, SM)));
(all_items = (() => { let item, side; const result = []; for (side of __py.iter(s.sides)) { for (item of __py.iter(side.items)) { result.push(item); }} return result; })());
(longest = __py.max((() => { let item, word; const result = []; for (item of __py.iter(all_items)) { for (word of __py.iter(__py.method(item.label, "split"))) { result.push(text_width(word, b.label_pt, true, __py.method(b, "family", b.label_pt, true))); }} return result; })(), __py.kw({default: 0})));
(minimum_lw = __py.max(__py.at(col(0, 2), 1), __py.bin("Add", __py.bin("Add", longest, SM), 2)));
(options = (() => { let step; const result = []; for (step of __py.iter(__py.range(25))) { if (!__py.truth((__py.cmp("Lt", __py.bin("Add", minimum_lw, __py.bin("Mult", step, XS)), __py.bin("Sub", __py.bin("Sub", inner, MD), __py.at(col(0, 2), 1)))))) continue; result.push(__py.bin("Add", minimum_lw, __py.bin("Mult", step, XS))); } return result; })());
function total_height(...__args) {
var [label_width] = __py.bind(__args, ["label_width"], [undefined], false, false);
var detail_width, j, side;
(detail_width = __py.bin("Sub", __py.bin("Sub", inner, label_width), MD));
return __py.sum((() => { let j; const result = []; for (j of __py.iter(__py.range(__py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.len(side.items)); } return result; })())))) { result.push(__py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { if (!__py.truth((__py.cmp("Lt", j, __py.len(side.items))))) continue; result.push(__py.max(__py.method(b, "height", __py.at(side.items, j).label, label_width, b.label_pt, true), __py.method(b, "height", __py.or([() => __py.at(side.items, j).detail, () => ""]), detail_width, b.body_pt))); } return result; })(), __py.kw({default: 0}))); } return result; })());
}
(lw = __py.min(__py.or([() => options, () => [minimum_lw]]), __py.kw({key: total_height})));
(dw = __py.bin("Sub", __py.bin("Sub", inner, lw), MD));
(nh = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.method(b, "height", side.name, inner, b.label_pt, true)); } return result; })()));
(count = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.len(side.items)); } return result; })()));
(heights = (() => { let j; const result = []; for (j of __py.iter(__py.range(count))) { result.push(__py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { if (!__py.truth((__py.cmp("Lt", j, __py.len(side.items))))) continue; result.push(__py.max(__py.method(b, "height", __py.at(side.items, j).label, lw, b.label_pt, true), __py.method(b, "height", __py.or([() => __py.at(side.items, j).detail, () => ""]), dw, b.body_pt))); } return result; })(), __py.kw({default: 0}))); } return result; })());
(body_top = __py.bin("Add", __py.bin("Add", top, nh), XS));
(natural = __py.bin("Add", __py.sum(heights), __py.bin("Mult", XS, __py.bin("Sub", count, 1))));
([y, height] = distribute(body_top, natural, count));
(gap = __py.max(XS, __py.bin("Div", __py.bin("Sub", height, __py.sum(heights)), __py.max(1, __py.bin("Sub", count, 1)))));
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
([x, _] = col(__py.bin("Mult", k, 6), 6));
__py.method(b, "rect", "cabecalho", x, top, cw, __py.bin("Add", nh, SM), __py.at(p, "soft"), __py.kw({rounded: __py.bool(b.style.raio)}));
__py.method(b, "text", "lado", side.name, __py.bin("Add", x, SM), __py.bin("Add", top, XS), inner, nh, b.label_pt, __py.at(p, "text"), __py.kw({bold: true, align: "center", path: (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name")}));
(cy = y);
for ([j, item] of __py.iter(__py.enumerate(side.items))) {
(path = (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1)));
__py.method(b, "fitted", "rotulo", item.label, __py.bin("Add", x, SM), cy, lw, __py.bin("Sub", CONTENT_BOTTOM, cy), [b.label_pt], __py.at(p, "text"), __py.kw({bold: true, path: __py.bin("Add", path, ".label")}));
if (__py.truth(item.detail)) {
__py.method(b, "fitted", "detalhe", item.detail, __py.bin("Add", __py.bin("Add", __py.bin("Add", x, SM), lw), MD), cy, dw, __py.bin("Sub", CONTENT_BOTTOM, cy), [b.body_pt], __py.at(p, "muted"), __py.kw({role: "corpo", path: __py.bin("Add", path, ".detail")}));
}
cy = __py.bin("Add", cy, __py.bin("Add", __py.at(heights, j), gap));
}
}
}

function layout_comparacao(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var _, count, cw, cy, dh, header_h, height, heights, inner, item, j, k, lh, natural, nh, p, row_heights, side, text, texts, values, x, y;
if (__py.truth((__py.cmp("Eq", b.variant, "comparison_columns")))) {
return comparison_columns(b, s, base, deck, top);
}
if (__py.truth((__py.cmp("Eq", b.variant, "comparison_text")))) {
([_, cw] = col(0, 6));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, SM)));
(count = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.len(side.items)); } return result; })()));
(nh = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.method(b, "height", side.name, inner, b.label_pt, true)); } return result; })()));
(texts = (() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push((() => { let item; const result = []; for (item of __py.iter(side.items)) { result.push(__py.bin("Add", item.label, (__py.truth(item.detail) ? __py.bin("Add", " — ", item.detail) : ""))); } return result; })()); } return result; })());
(heights = (() => { let j; const result = []; for (j of __py.iter(__py.range(count))) { result.push(__py.max((() => { let values; const result = []; for (values of __py.iter(texts)) { if (!__py.truth((__py.cmp("Lt", j, __py.len(values))))) continue; result.push(__py.method(b, "height", __py.at(values, j), inner, b.body_pt)); } return result; })(), __py.kw({default: 0}))); } return result; })());
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
([x, _] = col(__py.bin("Mult", k, 6), 6));
__py.method(b, "text", "lado", side.name, __py.bin("Add", x, SM), top, inner, nh, b.label_pt, __py.at(b.palette, "primary"), __py.kw({bold: true, path: (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name")}));
(y = __py.bin("Add", __py.bin("Add", top, nh), RULE));
for ([j, text] of __py.iter(__py.enumerate(__py.at(texts, k)))) {
__py.method(b, "fitted", "par", text, __py.bin("Add", x, SM), y, inner, __py.bin("Sub", CONTENT_BOTTOM, y), [b.body_pt], __py.at(b.palette, "text"), __py.kw({role: "corpo", path: (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1))}));
y = __py.bin("Add", y, __py.bin("Add", __py.at(heights, j), RULE));
}
}
return null;
}
(p = b.palette);
([_, cw] = col(0, 6));
(count = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.len(side.items)); } return result; })()));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, LG)));
(header_h = __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { result.push(__py.method(b, "height", side.name, inner, b.label_pt, true)); } return result; })()));
(row_heights = []);
for (j of __py.iter(__py.range(count))) {
__py.method(row_heights, "append", __py.max((() => { let side; const result = []; for (side of __py.iter(s.sides)) { if (!__py.truth((__py.cmp("Lt", j, __py.len(side.items))))) continue; result.push(__py.bin("Add", __py.bin("Add", __py.method(b, "height", __py.at(side.items, j).label, inner, b.label_pt, true), LABEL_GAP), (__py.truth(__py.at(side.items, j).detail) ? __py.method(b, "height", __py.at(side.items, j).detail, inner, b.body_pt) : 0))); } return result; })(), __py.kw({default: 0})));
}
(natural = __py.bin("Add", __py.bin("Add", __py.bin("Add", header_h, LG), __py.sum(row_heights)), __py.bin("Mult", MD, __py.bin("Sub", count, 1))));
([y, height] = distribute(top, natural, count));
for ([k, side] of __py.iter(__py.enumerate(s.sides))) {
([x, _] = col(__py.bin("Mult", k, 6), 6));
__py.method(b, "text", "lado", side.name, __py.bin("Add", x, LG), y, inner, header_h, b.label_pt, __py.at(p, "primary"), __py.kw({bold: true, path: (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".name")}));
(cy = __py.bin("Add", __py.bin("Add", y, header_h), LG));
for ([j, item] of __py.iter(__py.enumerate(side.items))) {
__py.method(b, "rect", "separador", x, __py.bin("Sub", cy, XS), cw, RULE, __py.at(p, "line"));
(lh = __py.method(b, "height", item.label, inner, b.label_pt, true));
(dh = (__py.truth(item.detail) ? __py.method(b, "height", item.detail, inner, b.body_pt) : 0));
draw_item(b, item, item.label, (__py.format(base, "", -1) + ".sides." + __py.format(k, "", -1) + ".items." + __py.format(j, "", -1)), __py.bin("Add", x, LG), cy, inner, __py.bin("Sub", CONTENT_BOTTOM, cy), lh, dh);
cy = __py.bin("Add", cy, __py.bin("Add", __py.at(row_heights, j), MD));
}
}
}

var ARROWS;
(ARROWS = "→↘↓↙←↖↑↗");

var BADGE;
(BADGE = 20);

function diagram_sizes_options(...__args) {
var [b] = __py.bind(__args, ["b"], [undefined], false, false);
var k, o, options;

(options = [[b.label_pt, b.body_pt], [__py.bin("Sub", b.label_pt, 2), __py.bin("Sub", b.body_pt, 2)], [MIN_LABEL_PT, MIN_BODY_PT]]);
return (() => { let k, o; const result = []; for ([k, o] of __py.iter(__py.enumerate(options))) { if (!__py.truth(__py.and([() => (__py.cmp("NotIn", o, __py.slice(options, null, k, null))), () => (__py.cmp("GtE", __py.at(o, 0), MIN_LABEL_PT)), () => (__py.cmp("GtE", __py.at(o, 1), MIN_BODY_PT))]))) continue; result.push(o); } return result; })();
}

function arrow_glyph(...__args) {
var [dx, dy] = __py.bind(__args, ["dx", "dy"], [undefined, undefined], false, false);

return __py.at(ARROWS, __py.bin("Mod", __py.round(__py.bin("Div", __py.math.atan2(dy, dx), __py.bin("Div", __py.math.pi, 4))), 8));
}

function diagram_content_height(...__args) {
var [b, items, w, ls, ds] = __py.bind(__args, ["b", "items", "w", "ls", "ds"], [undefined, undefined, undefined, undefined, undefined], false, false);
var detail_h, i, inner, label_h;

(inner = __py.bin("Sub", w, __py.bin("Mult", 2, SM)));
(label_h = __py.max((() => { let i; const result = []; for (i of __py.iter(items)) { result.push(__py.method(b, "height", i.label, inner, ls, true)); } return result; })()));
(detail_h = __py.max(__py.bin("Add", (() => { let i; const result = []; for (i of __py.iter(items)) { if (!__py.truth(i.detail)) continue; result.push(__py.method(b, "height", i.detail, inner, ds)); } return result; })(), [0])));
return __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Mult", 2, BADGE), XS), label_h), (__py.truth(detail_h) ? __py.bin("Add", XS, detail_h) : 0));
}

function diagram_box_height(...__args) {
var [b, items, w, ls, ds] = __py.bind(__args, ["b", "items", "w", "ls", "ds"], [undefined, undefined, undefined, undefined, undefined], false, false);
return __py.bin("Add", __py.bin("Add", SM, diagram_content_height(b, items, w, ls, ds)), SM);
}

function words_fit(...__args) {
var [b, items, w, ls, ds] = __py.bind(__args, ["b", "items", "w", "ls", "ds"], [undefined, undefined, undefined, undefined, undefined], false, false);
var i, room, word;

(room = __py.bin("Sub", __py.bin("Sub", w, __py.bin("Mult", 2, SM)), __py.bin("Mult", 2, __py.at(load_rules(), "text_padding"))));
for (i of __py.iter(items)) {
for (word of __py.iter(__py.method(i.label, "split"))) {
if (__py.truth((__py.cmp("Gt", text_width(word, ls, true, __py.method(b, "family", ls, true)), room)))) {
return false;
}
}
for (word of __py.iter(__py.method(__py.or([() => i.detail, () => ""]), "split"))) {
if (__py.truth((__py.cmp("Gt", text_width(word, ds, false, __py.method(b, "family", ds)), room)))) {
return false;
}
}
}
return true;
}

function diagram_sizes(...__args) {
var [b, items, w, max_h] = __py.bind(__args, ["b", "items", "w", "max_h"], [undefined, undefined, undefined, undefined], false, false);
var ds, h, ls;

for ([ls, ds] of __py.iter(diagram_sizes_options(b))) {
(h = diagram_box_height(b, items, w, ls, ds));
if (__py.truth(__py.and([() => (__py.cmp("LtE", h, max_h)), () => words_fit(b, items, w, ls, ds)]))) {
return [ls, ds, h];
}
}
return null;
}

function diagram_box(...__args) {
var [b, item, k, path, x, y, w, h, ls, ds, label_h, content_h] = __py.bind(__args, ["b", "item", "k", "path", "x", "y", "w", "h", "ls", "ds", "label_h", "content_h"], [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var dh, inner, lh, nh, p, ty;
(p = b.palette);
__py.method(b, "rect", "etapa", x, y, w, h, __py.at(p, "soft"), __py.kw({rounded: true}));
(y = __py.bin("Sub", __py.bin("Add", y, __py.bin("Div", __py.bin("Sub", h, content_h), 2)), SM));
__py.method(b, "rect", "numero_fundo", __py.bin("Sub", __py.bin("Add", x, __py.bin("Div", w, 2)), BADGE), __py.bin("Add", y, SM), __py.bin("Mult", 2, BADGE), __py.bin("Mult", 2, BADGE), __py.at(p, "primary"), __py.kw({rounded: true}));
(nh = __py.method(b, "height", __py.str(__py.bin("Add", k, 1)), __py.bin("Mult", 2, BADGE), 16, true));
__py.method(b, "text", "numero", __py.str(__py.bin("Add", k, 1)), __py.bin("Sub", __py.bin("Add", x, __py.bin("Div", w, 2)), BADGE), __py.bin("Sub", __py.bin("Add", __py.bin("Add", y, SM), BADGE), __py.bin("Div", nh, 2)), __py.bin("Mult", 2, BADGE), nh, 16, __py.at(p, "on_primary"), __py.kw({bold: true, align: "center"}));
(inner = __py.bin("Sub", w, __py.bin("Mult", 2, SM)));
(ty = __py.bin("Add", __py.bin("Add", __py.bin("Add", y, SM), __py.bin("Mult", 2, BADGE)), XS));
(lh = __py.method(b, "height", item.label, inner, ls, true));
__py.method(b, "text", "rotulo", item.label, __py.bin("Add", x, SM), ty, inner, lh, ls, __py.at(p, "text"), __py.kw({bold: true, align: "center", path: __py.bin("Add", path, ".label")}));
if (__py.truth(item.detail)) {
(dh = __py.method(b, "height", item.detail, inner, ds));
__py.method(b, "text", "detalhe", item.detail, __py.bin("Add", x, SM), __py.bin("Add", __py.bin("Add", ty, label_h), XS), inner, dh, ds, __py.at(p, "muted"), __py.kw({align: "center", path: __py.bin("Add", path, ".detail")}));
}
}

function diagram_arrow(...__args) {
var [b, x, y, glyph] = __py.bind(__args, ["b", "x", "y", "glyph"], [undefined, undefined, undefined, undefined], false, false);
var h;

(h = needed_height(glyph, XL, 24, true));
__py.method(b, "text", "seta", glyph, __py.bin("Sub", x, __py.bin("Div", XL, 2)), __py.bin("Sub", y, __py.bin("Div", h, 2)), XL, h, 24, __py.at(b.palette, "muted"), __py.kw({bold: true, align: "center"}));
}

function diagram_etapas(...__args) {
var [b, s, base, top] = __py.bind(__args, ["b", "s", "base", "top"], [undefined, undefined, undefined, undefined], false, false);
var content_h, ds, fit, h, i, item, k, label_h, ls, n, w, x, y;

(n = __py.len(s.items));
(w = __py.bin("Div", __py.bin("Sub", __py.bin("Sub", W, __py.bin("Mult", 2, M)), __py.bin("Mult", __py.bin("Sub", n, 1), XL)), n));
if (__py.truth((__py.cmp("Lt", w, 180)))) {
return false;
}
(fit = diagram_sizes(b, s.items, w, __py.bin("Sub", CONTENT_BOTTOM, top)));
if (__py.truth((__py.cmp("Is", fit, null)))) {
return false;
}
([ls, ds, h] = fit);
(label_h = __py.max((() => { let i; const result = []; for (i of __py.iter(s.items)) { result.push(__py.method(b, "height", i.label, __py.bin("Sub", w, __py.bin("Mult", 2, SM)), ls, true)); } return result; })()));
(content_h = diagram_content_height(b, s.items, w, ls, ds));
(h = __py.max(h, __py.bin("Mult", __py.bin("Sub", CONTENT_BOTTOM, top), 0.55)));
(y = card_position(top, h));
for ([k, item] of __py.iter(__py.enumerate(s.items))) {
(x = __py.bin("Add", M, __py.bin("Mult", k, __py.bin("Add", w, XL))));
if (__py.truth((__py.cmp("Lt", k, __py.bin("Sub", n, 1))))) {
diagram_arrow(b, __py.bin("Add", __py.bin("Add", x, w), __py.bin("Div", XL, 2)), __py.bin("Add", y, __py.bin("Div", h, 2)), "→");
}
diagram_box(b, item, k, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1)), x, y, w, h, ls, ds, label_h, content_h);
}
return true;
}

function clip_to_box(...__args) {
var [cx, cy, tx, ty, hw, hh] = __py.bind(__args, ["cx", "cy", "tx", "ty", "hw", "hh"], [undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var dx, dy, k, sx, sy;

([dx, dy] = [__py.bin("Sub", tx, cx), __py.bin("Sub", ty, cy)]);
(sx = (__py.truth(dx) ? __py.bin("Div", hw, __py.abs(dx)) : 1000000000.0));
(sy = (__py.truth(dy) ? __py.bin("Div", hh, __py.abs(dy)) : 1000000000.0));
(k = __py.min(sx, sy));
return [__py.bin("Add", cx, __py.bin("Mult", dx, k)), __py.bin("Add", cy, __py.bin("Mult", dy, k))];
}

function boxes_apart(...__args) {
var [a, c, gap] = __py.bind(__args, ["a", "c", "gap"], [undefined, undefined, undefined], false, false);
return __py.or([() => (__py.cmp("LtE", __py.bin("Add", __py.bin("Add", __py.at(a, 0), __py.at(a, 2)), gap), __py.at(c, 0))), () => (__py.cmp("LtE", __py.bin("Add", __py.bin("Add", __py.at(c, 0), __py.at(c, 2)), gap), __py.at(a, 0))), () => (__py.cmp("LtE", __py.bin("Add", __py.bin("Add", __py.at(a, 1), __py.at(a, 3)), gap), __py.at(c, 1))), () => (__py.cmp("LtE", __py.bin("Add", __py.bin("Add", __py.at(c, 1), __py.at(c, 3)), gap), __py.at(a, 1)))]);
}

function ciclo_geometry(...__args) {
var [n, bw, bh, top] = __py.bind(__args, ["n", "bw", "bh", "top"], [undefined, undefined, undefined, undefined], false, false);
var arrows, avail, ax, ay, box, boxes, centers, cx, cx0, cy, cy0, i, j, k, mx, my, rx, ry, spot, x1, x2, y1, y2;

(avail = __py.bin("Sub", CONTENT_BOTTOM, top));
([rx, ry] = [__py.bin("Div", __py.bin("Sub", __py.bin("Sub", W, __py.bin("Mult", 2, M)), bw), 2), __py.bin("Div", __py.bin("Sub", avail, bh), 2)]);
if (__py.truth((__py.cmp("LtE", ry, 0)))) {
return null;
}
([cx0, cy0] = [__py.bin("Div", W, 2), __py.bin("Add", top, __py.bin("Div", avail, 2))]);
(centers = (() => { let k; const result = []; for (k of __py.iter(__py.range(n))) { result.push([__py.bin("Add", cx0, __py.bin("Mult", rx, __py.math.sin(__py.bin("Div", __py.bin("Mult", __py.bin("Mult", 2, __py.math.pi), k), n)))), __py.bin("Sub", cy0, __py.bin("Mult", ry, __py.math.cos(__py.bin("Div", __py.bin("Mult", __py.bin("Mult", 2, __py.math.pi), k), n))))]); } return result; })());
(boxes = (() => { let cx, cy; const result = []; for ([cx, cy] of __py.iter(centers)) { result.push([__py.bin("Sub", cx, __py.bin("Div", bw, 2)), __py.bin("Sub", cy, __py.bin("Div", bh, 2)), bw, bh]); } return result; })());
for (i of __py.iter(__py.range(n))) {
for (j of __py.iter(__py.range(__py.bin("Add", i, 1), n))) {
if (__py.truth(!__py.truth(boxes_apart(__py.at(boxes, i), __py.at(boxes, j), MD)))) {
return null;
}
}
}
(arrows = []);
for (k of __py.iter(__py.range(n))) {
([[ax, ay], [cx, cy]] = [__py.at(centers, k), __py.at(centers, __py.bin("Mod", __py.bin("Add", k, 1), n))]);
([x1, y1] = clip_to_box(ax, ay, cx, cy, __py.bin("Div", bw, 2), __py.bin("Div", bh, 2)));
([x2, y2] = clip_to_box(cx, cy, ax, ay, __py.bin("Div", bw, 2), __py.bin("Div", bh, 2)));
([mx, my] = [__py.bin("Div", __py.bin("Add", x1, x2), 2), __py.bin("Div", __py.bin("Add", y1, y2), 2)]);
(spot = [__py.bin("Sub", mx, __py.bin("Div", XL, 2)), __py.bin("Sub", my, __py.bin("Div", XL, 2)), XL, XL]);
if (__py.truth(!__py.truth(__py.all((() => { let box; const result = []; for (box of __py.iter(boxes)) { result.push(boxes_apart(spot, box, 0)); } return result; })())))) {
return null;
}
__py.method(arrows, "append", [mx, my, arrow_glyph(__py.bin("Sub", cx, ax), __py.bin("Sub", cy, ay))]);
}
return [boxes, arrows];
}

function diagram_ciclo(...__args) {
var [b, s, base, top] = __py.bind(__args, ["b", "s", "base", "top"], [undefined, undefined, undefined, undefined], false, false);
var arrows, bh, boxes, bw, ds, geometry, glyph, i, item, k, label_h, ls, mx, my, n;

(n = __py.len(s.items));
if (__py.truth(!__py.truth((__py.cmp("LtE", 3, n) && __py.cmp("LtE", n, 5))))) {
return false;
}
for (bw of __py.iter((__py.truth((__py.cmp("LtE", n, 4))) ? [340, 300] : [280, 240]))) {
for ([ls, ds] of __py.iter(diagram_sizes_options(b))) {
if (__py.truth(!__py.truth(words_fit(b, s.items, bw, ls, ds)))) {
continue;
}
(bh = diagram_box_height(b, s.items, bw, ls, ds));
(geometry = ciclo_geometry(n, bw, bh, top));
if (__py.truth((__py.cmp("Is", geometry, null)))) {
continue;
}
([boxes, arrows] = geometry);
for ([mx, my, glyph] of __py.iter(arrows)) {
diagram_arrow(b, mx, my, glyph);
}
(label_h = __py.max((() => { let i; const result = []; for (i of __py.iter(s.items)) { result.push(__py.method(b, "height", i.label, __py.bin("Sub", bw, __py.bin("Mult", 2, SM)), ls, true)); } return result; })()));
for ([k, item] of __py.iter(__py.enumerate(s.items))) {
diagram_box(b, item, k, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1)), __py.at(__py.at(boxes, k), 0), __py.at(__py.at(boxes, k), 1), bw, bh, ls, ds, label_h, __py.bin("Sub", bh, __py.bin("Mult", 2, SM)));
}
return true;
}
}
return false;
}

function layout_etapas(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var original, w, x;
if (__py.truth((__py.truth(s.cycle) ? diagram_ciclo(b, s, base, top) : diagram_etapas(b, s, base, top)))) {
return null;
}

(original = b.style);
(b.style = __py.replace(b.style, __py.kw({marcador: "numero"})));
([x, w] = col(0, 12));
editorial_items(b, s.items, __py.bin("Add", base, ".items"), x, top, w, CONTENT_BOTTOM, [s.title]);
(b.style = original);
}

function layout_linha(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var gap, h, heights, k, lh, m, p, path, slot_width, text, texts, w, x, y;
(p = b.palette);
if (__py.truth((__py.cmp("GtE", __py.len(s.milestones), 4)))) {
(heights = (() => { let m; const result = []; for (m of __py.iter(s.milestones)) { result.push(__py.max(__py.method(b, "height", m.label, 320, b.label_pt, true), __py.method(b, "height", __py.or([() => m.detail, () => ""]), 640, b.body_pt), 52)); } return result; })());
if (__py.truth((__py.cmp("Gt", __py.bin("Add", __py.sum(heights), __py.bin("Mult", LABEL_GAP, __py.bin("Sub", __py.len(heights), 1))), __py.bin("Sub", CONTENT_BOTTOM, top))))) {
([x, w] = col(1, 11));
(texts = (() => { let m; const result = []; for (m of __py.iter(s.milestones)) { result.push(__py.bin("Add", m.label, (__py.truth(m.detail) ? __py.bin("Add", " — ", m.detail) : ""))); } return result; })());
(heights = (() => { let m, text; const result = []; for ([m, text] of __py.iter(__py.zip(s.milestones, texts))) { result.push(__py.max(__py.method(b, "height", text, w, b.body_pt), __py.method(b, "height", m.date, __py.bin("Add", __py.at(col(0), 1), XS), b.label_pt, true))); } return result; })());
(gap = __py.min(MD, __py.max(XS, __py.bin("Div", __py.bin("Sub", __py.bin("Sub", CONTENT_BOTTOM, top), __py.sum(heights)), __py.bin("Sub", __py.len(heights), 1)))));
(y = top);
for ([k, [m, text, h]] of __py.iter(__py.enumerate(__py.zip(s.milestones, texts, heights)))) {
(path = (__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1)));
__py.method(b, "fitted", "data", m.date, M, y, __py.bin("Add", __py.at(col(0), 1), XS), __py.bin("Sub", CONTENT_BOTTOM, y), [b.label_pt], __py.at(p, "primary"), __py.kw({bold: true, path: __py.bin("Add", path, ".date")}));
__py.method(b, "fitted", "marco", text, x, y, w, __py.bin("Sub", CONTENT_BOTTOM, y), [b.body_pt], __py.at(p, "text"), __py.kw({role: "corpo", path: path}));
y = __py.bin("Add", y, __py.bin("Add", h, gap));
}
return null;
}
(y = __py.bin("Add", top, __py.max(0, __py.bin("Div", __py.bin("Sub", __py.bin("Sub", __py.bin("Sub", CONTENT_BOTTOM, top), __py.sum(heights)), __py.bin("Mult", 12, __py.bin("Sub", __py.len(heights), 1))), 2))));
for ([k, [m, h]] of __py.iter(__py.enumerate(__py.zip(s.milestones, heights)))) {
(path = (__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1)));
__py.method(b, "fitted", "data", m.date, M, y, 140, h, [b.label_pt], __py.at(p, "primary"), __py.kw({bold: true, path: __py.bin("Add", path, ".date")}));
__py.method(b, "fitted", "rotulo", m.label, 224, y, 320, h, [b.label_pt], __py.at(p, "text"), __py.kw({bold: true, path: __py.bin("Add", path, ".label")}));
if (__py.truth(m.detail)) {
__py.method(b, "fitted", "detalhe", m.detail, 568, y, 648, h, [b.body_pt], __py.at(p, "muted"), __py.kw({path: __py.bin("Add", path, ".detail")}));
}
y = __py.bin("Add", y, __py.bin("Add", h, 12));
}
if (__py.truth((__py.cmp("Gt", __py.bin("Sub", y, 12), CONTENT_BOTTOM)))) {
__py.method(b, "fit", __py.method("\n", "join", (() => { let m; const result = []; for (m of __py.iter(s.milestones)) { result.push(m.label); } return result; })()), 320, __py.bin("Sub", CONTENT_BOTTOM, top), [b.label_pt], __py.kw({path: __py.bin("Add", base, ".milestones")}));
}
return null;
}
(slot_width = __py.bin("Div", __py.bin("Sub", W, __py.bin("Mult", 2, M)), __py.len(s.milestones)));
for ([k, m] of __py.iter(__py.enumerate(s.milestones))) {
(x = __py.bin("Add", M, __py.bin("Mult", k, slot_width)));
(path = (__py.format(base, "", -1) + ".milestones." + __py.format(k, "", -1)));
(h = __py.method(b, "fitted", "data", m.date, x, top, __py.bin("Sub", slot_width, 24), 80, [b.label_pt], __py.at(p, "primary"), __py.kw({bold: true, path: __py.bin("Add", path, ".date")})));
__py.method(b, "rect", "eixo", x, __py.bin("Add", __py.bin("Add", top, h), 12), __py.bin("Sub", slot_width, 24), 4, __py.at(p, "line"));
(lh = __py.method(b, "fitted", "rotulo", m.label, x, __py.bin("Add", __py.bin("Add", top, h), 40), __py.bin("Sub", slot_width, 24), 120, [b.label_pt], __py.at(p, "text"), __py.kw({bold: true, path: __py.bin("Add", path, ".label")})));
if (__py.truth(m.detail)) {
(y = __py.bin("Add", __py.bin("Add", __py.bin("Add", top, h), 44), lh));
__py.method(b, "fitted", "detalhe", m.detail, x, y, __py.bin("Sub", slot_width, 24), __py.bin("Sub", CONTENT_BOTTOM, y), [b.body_pt], __py.at(p, "muted"), __py.kw({path: __py.bin("Add", path, ".detail")}));
}
}
}

function layout_citacao(...__args) {
var [b, s, base, deck] = __py.bind(__args, ["b", "s", "base", "deck"], [undefined, undefined, undefined, undefined], false, false);
var p, th;
(p = b.palette);
__py.method(b, "rect", "painel", M, 120, __py.bin("Sub", W, __py.bin("Mult", 2, M)), 440, __py.at(p, "card"), __py.kw({rounded: true}));
__py.method(b, "rect", "barra", M, 120, 12, 440, __py.at(p, "primary"));
__py.method(b, "text", "aspas", "“", __py.bin("Add", M, 48), 128, 120, __py.method(b, "height", "“", 120, 96, true), 96, __py.at(p, "primary"), __py.kw({bold: true}));
(th = __py.method(b, "fitted", "citacao", s.text, __py.bin("Add", M, 64), 236, __py.bin("Sub", __py.bin("Sub", W, __py.bin("Mult", 2, M)), 128), 230, [34, 32, 30, 28, 26, 24], __py.at(p, "text"), __py.kw({path: (__py.format(base, "", -1) + ".text")})));
__py.method(b, "fitted", "autor", __py.bin("Add", "— ", s.author), __py.bin("Add", M, 64), __py.min(__py.bin("Add", __py.bin("Add", 236, th), 16), 480), __py.bin("Sub", __py.bin("Sub", W, __py.bin("Mult", 2, M)), 128), 60, [22, 20], __py.at(p, "muted"), __py.kw({align: "right", path: (__py.format(base, "", -1) + ".author")}));
}

function br_number(...__args) {
var [value] = __py.bind(__args, ["value"], [undefined], false, false);
var text;
(text = __py.method(__py.method((__py.format(value, (",.2f"), -1)), "rstrip", "0"), "rstrip", "."));
return __py.method(__py.method(__py.method(text, "replace", ",", "X"), "replace", ".", ","), "replace", "X", ".");
}

function layout_grafico(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var bar, bar_w, base_y, best, chart_h, h, k, label_h, ls, n, p, peak, slot, uh, value_h, x;
(p = b.palette);
(n = __py.len(s.bars));
if (__py.truth(s.unit)) {
(uh = __py.method(b, "height", s.unit, 900, 16));
__py.method(b, "text", "unidade", s.unit, M, __py.bin("Sub", top, 8), 900, uh, 16, __py.at(p, "muted"), __py.kw({path: (__py.format(base, "", -1) + ".unit")}));
top = __py.bin("Add", top, __py.bin("Sub", uh, 8));
}
(slot = __py.bin("Div", __py.bin("Sub", W, __py.bin("Mult", 2, M)), n));
([ls, label_h] = uniform(b, (() => { let k, x; const result = []; for ([k, x] of __py.iter(__py.enumerate(s.bars))) { result.push([x.label, (__py.format(base, "", -1) + ".bars." + __py.format(k, "", -1) + ".label")]); } return result; })(), __py.bin("Sub", slot, 8), 64, [24, 22, 20]));
(value_h = __py.method(b, "height", "0", 100, 20, true));
(base_y = __py.bin("Sub", __py.bin("Sub", CONTENT_BOTTOM, label_h), 6));
(chart_h = __py.bin("Sub", __py.bin("Sub", base_y, top), value_h));
(peak = __py.or([() => __py.max((() => { let x; const result = []; for (x of __py.iter(s.bars)) { result.push(x.value); } return result; })()), () => 1]));
(bar_w = __py.min(140, __py.bin("Mult", slot, 0.6)));
(best = __py.max(__py.range(n), __py.kw({key: (k) => __py.at(s.bars, k).value})));
__py.method(b, "rect", "base", M, base_y, __py.bin("Sub", W, __py.bin("Mult", 2, M)), 3, __py.at(p, "line"));
for ([k, bar] of __py.iter(__py.enumerate(s.bars))) {
(x = __py.bin("Add", __py.bin("Add", M, __py.bin("Mult", k, slot)), __py.bin("Div", __py.bin("Sub", slot, bar_w), 2)));
(h = __py.max(4, __py.bin("Div", __py.bin("Mult", chart_h, bar.value), peak)));
__py.method(b, "rect", "barra", x, __py.bin("Sub", base_y, h), bar_w, h, (__py.truth((__py.cmp("Eq", k, best))) ? __py.at(p, "accent") : __py.at(p, "primary")));
__py.method(b, "text", "valor", br_number(bar.value), __py.bin("Add", M, __py.bin("Mult", k, slot)), __py.bin("Sub", __py.bin("Sub", base_y, h), value_h), slot, value_h, 20, __py.at(p, "text"), __py.kw({bold: true, align: "center", path: (__py.format(base, "", -1) + ".bars." + __py.format(k, "", -1) + ".value")}));
__py.method(b, "text", "rotulo", bar.label, __py.bin("Add", __py.bin("Add", M, __py.bin("Mult", k, slot)), 4), __py.bin("Add", base_y, 6), __py.bin("Sub", slot, 8), label_h, ls, __py.at(p, "muted"), __py.kw({align: "center", path: (__py.format(base, "", -1) + ".bars." + __py.format(k, "", -1) + ".label")}));
}
}

function layout_imagem(...__args) {
var [b, s, base, deck, top, root] = __py.bind(__args, ["b", "s", "base", "deck", "top", "root"], [undefined, undefined, undefined, undefined, undefined, undefined], false, false);
var dh, gap, height, heights, i, item, k, lh, message, natural, w, x, y;
if (__py.truth(!__py.truth(s.image_file))) {
__py.method(b.diagnostics, "append", Diagnostic(__py.kw({code: "A011", severity: "AVISO", message: "Imagem não resolvida; composição textual.", slide: b.number, evidence: ({["path"]: (__py.format(base, "", -1) + ".image_query"), ["query"]: s.image_query})})));
if (__py.truth(s.items)) {
return editorial_items(b, s.items, __py.bin("Add", base, ".items"), M, top, __py.bin("Sub", W, __py.bin("Mult", 2, M)), CONTENT_BOTTOM, [s.title], __py.kw({cards: true}));
}
(message = __py.or([() => s.caption, () => s.title, () => ""]));
__py.method(b, "fitted", "destaque", message, __py.bin("Add", M, LG), __py.bin("Add", top, LG), __py.bin("Sub", __py.bin("Sub", W, __py.bin("Mult", 2, M)), __py.bin("Mult", 2, LG)), __py.bin("Sub", __py.bin("Sub", CONTENT_BOTTOM, top), __py.bin("Mult", 2, LG)), [48, 42, 36], __py.at(b.palette, "primary"), __py.kw({path: __py.bin("Add", base, ".caption")}));
return null;
}
if (__py.truth((__py.cmp("Eq", b.variant, "photo_text")))) {
photo(b, s, base, top);
return layout_topicos(b, s, base, deck, top);
}
photo(b, s, base, top);
([x, w] = col(0, (__py.truth((__py.cmp("Eq", b.variant, "photo50"))) ? 6 : 7)));
(heights = (() => { let i; const result = []; for (i of __py.iter(s.items)) { result.push([__py.method(b, "height", i.label, __py.bin("Sub", w, LG), b.label_pt, true), (__py.truth(i.detail) ? __py.method(b, "height", i.detail, __py.bin("Sub", w, LG), b.body_pt) : 0)]); } return result; })());
(natural = __py.bin("Add", __py.sum((() => { let dh, lh; const result = []; for ([lh, dh] of __py.iter(heights)) { result.push(__py.bin("Add", __py.bin("Add", lh, dh), LABEL_GAP)); } return result; })()), __py.bin("Mult", MD, __py.max(0, __py.bin("Sub", __py.len(heights), 1)))));
([y, height] = distribute(top, natural, __py.len(heights)));
(gap = __py.max(XS, __py.bin("Div", __py.bin("Sub", height, __py.sum((() => { let dh, lh; const result = []; for ([lh, dh] of __py.iter(heights)) { result.push(__py.bin("Add", __py.bin("Add", lh, dh), LABEL_GAP)); } return result; })())), __py.max(1, __py.bin("Sub", __py.len(heights), 1)))));
for ([k, [item, [lh, dh]]] of __py.iter(__py.enumerate(__py.zip(s.items, heights)))) {
draw_item(b, item, item.label, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1)), x, y, __py.bin("Sub", w, LG), __py.bin("Sub", CONTENT_BOTTOM, y), lh, dh);
y = __py.bin("Add", y, __py.bin("Add", __py.bin("Add", __py.bin("Add", lh, dh), LABEL_GAP), gap));
}
}

function layout_conclusao(...__args) {
var [b, s, base, deck, top] = __py.bind(__args, ["b", "s", "base", "deck", "top"], [undefined, undefined, undefined, undefined, undefined], false, false);
var cw, cx, dh, h, i, inner, item, items, k, lh, nh, number_size, original, p, w, x, y;

([p, items] = [b.palette, s.items]);
([x, w] = col(0, 12));
if (__py.truth((__py.cmp("Eq", b.variant, "actions_columns")))) {
(cw = __py.bin("Div", __py.bin("Sub", w, __py.bin("Mult", MD, __py.bin("Sub", __py.len(items), 1))), __py.max(1, __py.len(items))));
(inner = __py.bin("Sub", cw, __py.bin("Mult", 2, LG)));
(lh = __py.max((() => { let i; const result = []; for (i of __py.iter(items)) { result.push(__py.method(b, "height", i.label, inner, b.label_pt, true)); } return result; })(), __py.kw({default: 0})));
(dh = __py.max((() => { let i; const result = []; for (i of __py.iter(items)) { result.push((__py.truth(i.detail) ? __py.method(b, "height", i.detail, inner, b.body_pt) : 0)); } return result; })(), __py.kw({default: 0})));
(number_size = 32);
(nh = __py.method(b, "height", "00", inner, number_size, true));
(h = __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Add", __py.bin("Mult", 2, LG), nh), LABEL_GAP), lh), LABEL_GAP), dh));
(y = card_position(top, h));
check_block_bottom(b, y, h, CONTENT_BOTTOM, __py.bin("Add", base, ".items"));
for ([k, item] of __py.iter(__py.enumerate(items))) {
(cx = __py.bin("Add", x, __py.bin("Mult", k, __py.bin("Add", cw, MD))));
__py.method(b, "card", cx, y, cw, h, __py.kw({accent: true}));
__py.method(b, "text", "acao", (__py.format(__py.bin("Add", k, 1), ("02d"), -1)), __py.bin("Add", cx, LG), __py.bin("Add", y, LG), inner, nh, number_size, __py.at(p, "primary"), __py.kw({bold: true}));
draw_item(b, item, item.label, (__py.format(base, "", -1) + ".items." + __py.format(k, "", -1)), __py.bin("Add", cx, LG), __py.bin("Add", __py.bin("Add", __py.bin("Add", y, LG), nh), LABEL_GAP), inner, __py.bin("Sub", __py.bin("Sub", __py.bin("Sub", h, __py.bin("Mult", 2, LG)), nh), LABEL_GAP), lh, dh);
}
} else {

(original = b.style);
(b.style = __py.replace(b.style, __py.kw({marcador: "numero"})));
editorial_items(b, items, __py.bin("Add", base, ".items"), x, __py.bin("Add", top, LG), w, CONTENT_BOTTOM, [s.title]);
(b.style = original);
}
}

function full_notes(...__args) {
var [s, facts] = __py.bind(__args, ["s", "facts"], [undefined, undefined], false, false);
var fact, parts, ref, refs;
(parts = (__py.truth(s.notes) ? [s.notes] : []));
(refs = []);
for (ref of __py.iter(s.sources)) {
(fact = __py.method(facts, "get", ref));
if (__py.truth(fact)) {
__py.method(refs, "append", ("[" + __py.format(ref, "", -1) + "] " + __py.format(__py.method(fact, "get", "claim", ""), "", -1) + " — " + __py.format(__py.method(fact, "get", "source_title", ""), "", -1) + " — " + __py.format(__py.method(fact, "get", "url", ""), "", -1)));
} else {
__py.method(refs, "append", ref);
}
}
if (__py.truth(refs)) {
__py.method(parts, "append", __py.bin("Add", "Fontes:\n", __py.method("\n", "join", refs)));
}
return __py.or([() => __py.method("\n\n", "join", parts), () => null]);
}

function alto_to_ast(...__args) {
var [deck, facts, root] = __py.bind(__args, ["deck", "facts", "root"], [undefined, null, null], false, false);
var b, base, base_theme, blocked, c, candidates, chosen, compact, compact_profile, d, dense, diagnostics, ds, feature_palette, history, i, k, mapping, metrics, n, palette, pool, preferred, previous, previous_visual, probe, s, short_cards, slide_palette, slides, style, top, total, v, variant, visual;



(facts = __py.or([() => facts, () => ({})]));
(style = __py.at(STYLES, deck.theme));
([palette, feature_palette, base_theme] = [style.comum, style.destaque, style.tema]);
([slides, mapping, diagnostics] = [[], ({}), []]);
([previous, previous_visual] = [null, null]);
(history = []);
(total = __py.len(deck.slides));
for ([n, s] of __py.iter(__py.enumerate(deck.slides, 1))) {
(dense = __py.or([() => (__py.cmp("Eq", s.kind, "comparacao")), () => __py.and([() => (__py.cmp("Eq", s.kind, "linha_do_tempo")), () => (__py.cmp("GtE", __py.len(s.milestones), 4))]), () => (__py.cmp("GtE", __py.len(s.items), 4))]));
(slide_palette = (__py.truth((__py.cmp("In", s.kind, FEATURE_KINDS))) ? feature_palette : palette));
(candidates = []);
for ([variant, compact_profile] of __py.iter((() => { let compact, v; const result = []; for (v of __py.iter(variants_for(s, root))) { for (compact of __py.iter((__py.truth(dense) ? [true] : [false, true]))) { result.push([v, compact]); }} return result; })())) {
(b = new Builder(n, slide_palette, __py.kw({label_pt: optical_size((__py.truth(compact_profile) ? 20 : OPTICAL_LABEL_PT), style.fonte_corpo, MIN_LABEL_PT), body_pt: optical_size((__py.truth(compact_profile) ? 18 : BODY_PT), style.fonte_corpo, MIN_BODY_PT, __py.kw({effective_minimum: 18})), style: style, variant: variant, root: root})));
if (__py.truth((__py.cmp("NotEq", __py.method(__py.at(slide_palette, "bg"), "upper"), __py.method(__py.at(RENDER_BG, base_theme), "upper"))))) {
__py.method(b, "rect", "fundo", 0, 0, W, H, __py.at(slide_palette, "bg"), __py.kw({role: "background"}));
}
(base = ("slides." + __py.format(__py.bin("Sub", n, 1), "", -1)));
if (__py.truth((__py.cmp("Eq", s.kind, "capa")))) {
layout_capa(b, s, base, deck);
} else {
if (__py.truth((__py.cmp("Eq", s.kind, "secao")))) {
layout_secao(b, s, base, deck);
} else {
if (__py.truth((__py.cmp("Eq", s.kind, "citacao")))) {
layout_citacao(b, s, base, deck);
footer(b, s, facts, total);
} else {
(top = header(b, s, base));
__py.method(({["topicos"]: layout_topicos, ["numeros"]: layout_numeros, ["comparacao"]: layout_comparacao, ["etapas"]: layout_etapas, ["linha_do_tempo"]: layout_linha, ["grafico"]: layout_grafico, ["conclusao"]: layout_conclusao}), "get", s.kind, (...a) => layout_imagem(...__py.iter(a), root))(b, s, base, deck, top);
footer(b, s, facts, total);
}
}
}
__py.method(b, "notes", full_notes(s, facts));
(visual = (__py.truth((__py.cmp("In", variant, new Set(["cards", "grid", "number_columns"])))) ? "cards" : (__py.truth((__py.cmp("In", variant, new Set(["rows", "number_rows", "etapas", "actions_rows"])))) ? "rows" : variant)));
try {
(probe = analyze(PresentationNode(__py.kw({title: deck.title, theme: base_theme, slides: [SlideNode(__py.kw({number: 1, commands: b.commands}))]})), root));
(__py.at(probe.slides, 0).number = n);
(ds = check_design(probe));
(metrics = score_slide(__py.at(probe.slides, 0), variant, previous, visual, previous_visual, history));
(metrics = content_preference(metrics, s.kind, s.items));
} catch (exc) {
(ds = exc.diagnostics);
(metrics = __py.dict(__py.kw({variant: variant, visual: visual, occupancy: 0.0, scores: ({}), score: 0.0})));
}
(blocked = (() => { let d; const result = []; for (d of __py.iter(__py.bin("Add", b.diagnostics, ds))) { if (!__py.truth(__py.and([() => (__py.cmp("NotEq", d.severity, "INFORMAÇÃO")), () => __py.or([() => (__py.cmp("In", d.code, BLOCKERS)), () => (__py.cmp("Eq", d.severity, "ERRO"))])]))) continue; result.push(d); } return result; })());
__py.method(candidates, "append", __py.dict(__py.kw({...metrics, valid: !__py.truth(blocked), builder: b, blockers: (() => { let d; const result = []; for (d of __py.iter(blocked)) { result.push(__py.method(d, "model_dump")); } return result; })()})));
}
(candidates = (() => { let variant; const result = []; for (variant of __py.iter(variants_for(s, root))) { result.push(__py.next((() => { let c; const result = []; for (c of __py.iter(candidates)) { if (!__py.truth(__py.and([() => (__py.cmp("Eq", __py.at(c, "variant"), variant)), () => __py.at(c, "valid")]))) continue; result.push(c); } return result; })(), __py.next((() => { let c; const result = []; for (c of __py.iter(candidates)) { if (!__py.truth((__py.cmp("Eq", __py.at(c, "variant"), variant)))) continue; result.push(c); } return result; })()))); } return result; })());
if (__py.truth(__py.any((() => { let c; const result = []; for (c of __py.iter(candidates)) { result.push(__py.and([() => __py.at(c, "valid"), () => (__py.cmp("In", __py.at(c, "variant"), new Set(["comparison_columns", "comparison_pairs"])))])); } return result; })()))) {
(candidates = (() => { let c; const result = []; for (c of __py.iter(candidates)) { if (!__py.truth((__py.cmp("NotEq", __py.at(c, "variant"), "comparison_text")))) continue; result.push(c); } return result; })());
}
(short_cards = __py.and([() => (__py.cmp("Eq", s.kind, "topicos")), () => (__py.cmp("LtE", 2, __py.len(s.items)) && __py.cmp("LtE", __py.len(s.items), 3)), () => __py.all((() => { let i; const result = []; for (i of __py.iter(s.items)) { result.push(__py.and([() => (__py.cmp("LtE", __py.len(i.label), 36)), () => (__py.cmp("LtE", __py.len(__py.or([() => i.detail, () => ""])), 110))])); } return result; })())]));
(preferred = (__py.truth((__py.cmp("Eq", s.kind, "conclusao"))) ? "actions_columns" : (__py.truth(short_cards) ? "cards" : null)));
(pool = (() => { let c; const result = []; for (c of __py.iter(candidates)) { if (!__py.truth(__py.and([() => (__py.cmp("Eq", __py.at(c, "variant"), preferred)), () => __py.at(c, "valid"), () => (__py.cmp("NotEq", __py.at(c, "variant"), previous))]))) continue; result.push(c); } return result; })());
(chosen = choose(__py.or([() => pool, () => candidates]), previous));
(b = __py.at(chosen, "builder"));
if (__py.truth(__py.and([() => !__py.truth(__py.at(chosen, "valid")), () => !__py.truth(__py.any((() => { let d; const result = []; for (d of __py.iter(b.diagnostics)) { result.push((__py.cmp("Eq", d.severity, "ERRO"))); } return result; })()))]))) {
__py.method(b.diagnostics, "append", Diagnostic(__py.kw({code: "A010", severity: "ERRO", slide: n, message: "Nenhuma variante comporta o conteúdo nas restrições de design.", evidence: ({["path"]: ("slides." + __py.format(__py.bin("Sub", n, 1), "", -1)), ["blockers"]: __py.at(chosen, "blockers")})})));
}
__py.method(b.diagnostics, "append", Diagnostic(__py.kw({code: "A030", severity: "INFORMAÇÃO", slide: n, message: "Variante escolhida por heurística geométrica determinística.", evidence: ({...(() => { let k; const result = []; for (k of __py.iter(["variant", "visual", "score", "scores", "occupancy", "valid"])) { result.push([k, __py.at(chosen, k)]); } return Object.fromEntries(result); })(), ["diversity_bonus"]: __py.method(chosen, "get", "diversity_bonus", 0.0), ["content_bonus"]: __py.method(chosen, "get", "content_bonus", 0.0), ["label_pt"]: b.label_pt, ["body_pt"]: b.body_pt, ["selection_policy"]: (__py.truth(pool) ? "content" : "geometry"), ["recent_variants"]: __py.slice(history, -(3), null, null), ["candidates"]: (() => { let c; const result = []; for (c of __py.iter(candidates)) { result.push((() => { let k; const result = []; for (k of __py.iter(["variant", "visual", "score", "scores", "occupancy", "valid", "blockers"])) { result.push([k, __py.at(c, k)]); } return Object.fromEntries(result); })()); } return result; })()})})));
__py.method(slides, "append", SlideNode(__py.kw({number: n, commands: b.commands})));
__py.method(mapping, "update", (() => { let k, v; const result = []; for ([k, v] of __py.iter(__py.method(b.mapping, "items"))) { result.push([(__py.format(n, "", -1) + ":" + __py.format(k, "", -1)), v]); } return Object.fromEntries(result); })());
diagnostics = __py.bin("Add", diagnostics, b.diagnostics);
([previous, previous_visual] = [__py.at(chosen, "variant"), __py.at(chosen, "visual")]);
__py.method(history, "append", previous);
}
return [PresentationNode(__py.kw({title: deck.title, theme: base_theme, slides: slides})), mapping, diagnostics];
}

import { photo, variants_for } from './images.js';

export { box, intersection, area, union_area, distance, bounds, resolve_position, aligned_position, translate, resize_group, TITLE_PT, LABEL_PT, BODY_PT, CREDIT_PT, MIN_TITLE_PT, MIN_LABEL_PT, MIN_BODY_PT, MIN_SUBTITLE_PT, proper_words, SINGLE_LOWER, sentence_case, capitalize_first, normalized, distinct_label, visible_labels, ordered_steps, balanced_title, composition, WIDTH, HEIGHT, MARGIN, RIGHT, GUTTER, SPACES, XS, SM, MD, LG, XL, XXL, TITLE_Y, CONTENT_BOTTOM, CARD_PADDING, LABEL_GAP, RULE, OPTICAL_CENTER, MIN_BLOCK_FRACTION, OPTICAL_LABEL_PT, COL_WIDTH, card_position, col, distribute, Estilo, title_style, luminance, contrast, known_background, estimated_overflow, check_design, WEIGHTS, BLOCKERS, occupancy, occupation_score, balance, alignment, regularity, rhythm, aggregate, useful_elements, score_slide, content_preference, choose, OCCUPANCY_MINIMUM, content_occupancy, LIMITS, TEXT_LIMITS, GENERIC, _digits, number_tokens, _norm, validate_alto, PALETTES, _palette, _PALETTE_STYLES, STYLE_ATTRIBUTES, STYLES, RENDER_BG, FEATURE_KINDS, needed_height, Builder, source_label, header, LABELED_REF, footer, uniform, label_detail_sizes, layout_capa, layout_secao, editorial_items, check_block_bottom, draw_item, layout_topicos, layout_numeros, comparison_columns, layout_comparacao, ARROWS, BADGE, diagram_sizes_options, arrow_glyph, diagram_content_height, diagram_box_height, words_fit, diagram_sizes, diagram_box, diagram_arrow, diagram_etapas, clip_to_box, boxes_apart, ciclo_geometry, diagram_ciclo, layout_etapas, layout_linha, layout_citacao, br_number, layout_grafico, layout_imagem, layout_conclusao, full_notes, alto_to_ast };
