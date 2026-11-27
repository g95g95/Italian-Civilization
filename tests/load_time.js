// Phase 6 gate: time from navigation to the first full map paint on an emulated mid-range phone.
// Emulation follows Lighthouse's mobile defaults: 4x CPU slowdown, 150 ms RTT, 1.6 Mbps down.
// The page is served gzip-compressed, as any static host does. Prints the time in ms.
const http = require('http'), fs = require('fs'), path = require('path'), zlib = require('zlib');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..', 'web');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css' };
const srv = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream', 'Content-Encoding': 'gzip' });
  res.end(zlib.gzipSync(fs.readFileSync(p)));
});
srv.listen(0, async () => {
  const port = srv.address().port;
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 412, height: 860 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());  // external fonts are optional (fallback stack)
  const cdp = await ctx.newCDPSession(p);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1638.4 * 1024 / 8, uploadThroughput: 675 * 1024 / 8 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(`http://localhost:${port}/`, { waitUntil: 'commit' });
  await p.waitForFunction(() => window.__civReady, null, { timeout: 30000, polling: 50 });
  const ms = await p.evaluate(() => window.__civReady);
  console.log(JSON.stringify({ ms: Math.round(ms), errors: errs }));
  await b.close(); srv.close();
});
