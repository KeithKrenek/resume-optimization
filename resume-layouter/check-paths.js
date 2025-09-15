try {
  console.log("Node is looking for 'puppeteer' in these locations:");
  console.log(require.resolve.paths('puppeteer'));
} catch (e) {
  console.error(e);
}