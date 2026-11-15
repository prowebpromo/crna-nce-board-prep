// Local smoke-test server. Pages continues to publish the static files directly.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';

const index = await readFile(new URL('../index.html', import.meta.url));
createServer((request, response) => {
  if (request.url !== '/' && request.url !== '/index.html') {
    response.writeHead(404).end();
    return;
  }
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }).end(index);
}).listen(4173, '127.0.0.1');
