// find-file.js
try {
  const filePath = require.resolve('puppeteer');
  console.log('Node is loading the library from this exact file path:');
  console.log(filePath);
} catch (e) {
  console.error('ERROR: Node could not find the puppeteer package at all.', e);
}