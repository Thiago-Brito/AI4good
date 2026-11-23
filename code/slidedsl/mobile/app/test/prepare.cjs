const fs = require('node:fs');
fs.mkdirSync('outputs/tests', {recursive: true});
fs.writeFileSync('outputs/tests/package.json', JSON.stringify({type: 'module'}));