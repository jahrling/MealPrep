#!/usr/bin/env python3
"""Standalone backend for the Our Dinner Table planner.

Serves dinnertable.html and a small JSON API backed by SQLite, standing in
for the Claude Artifact db/sample capabilities the app was prototyped with.
No third-party dependencies -- stdlib only.

Config via environment variables, or a .env file next to this script:
  PORT               port to listen on (default 8002)
  DB_PATH            SQLite file location (default mealplan.db next to this script)
  ANTHROPIC_API_KEY  enables the AI features (recipe ideas, week planning,
                      fridge photo scanning). Without it, those buttons show
                      a message instead of erroring.
  ANTHROPIC_MODEL     model id to call (default claude-sonnet-5)
  OLLAMA_VISION_MODEL local vision model (e.g. qwen3.5:9b). When set, requests
                      that include photos go to Ollama instead of Anthropic,
                      so inventory scans stay on the home network.
  OLLAMA_URL          Ollama endpoint (default http://localhost:11434)

Recipe import fetches pasted links server-side (/api/fetch-page), only to
public internet addresses.
"""
import ipaddress
import json
import os
import re
import socket
import sqlite3
import sys
import threading
import time
import uuid
import zlib
import urllib.error
import urllib.request
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DB_PATH') or os.path.join(BASE_DIR, 'mealplan.db')
HTML_PATH = os.path.join(BASE_DIR, 'dinnertable.html')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
# URL path -> (file in static/, content type). Icons and the web-app manifest.
STATIC_FILES = {
    '/manifest.webmanifest': ('manifest.webmanifest', 'application/manifest+json'),
    '/icon.svg': ('icon.svg', 'image/svg+xml'),
    '/icon-192.png': ('icon-192.png', 'image/png'),
    '/icon-512.png': ('icon-512.png', 'image/png'),
    '/icon-maskable-512.png': ('icon-maskable-512.png', 'image/png'),
    '/apple-touch-icon.png': ('apple-touch-icon.png', 'image/png'),
    '/favicon-32.png': ('favicon-32.png', 'image/png'),
}
ENV_PATH = os.path.join(BASE_DIR, '.env')


def load_dotenv(path):
    """Minimal .env loader: KEY=VALUE per line, '#' comments, no expansion.
    Real environment variables always win over the file."""
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip()
            if value and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ.setdefault(key, value)


load_dotenv(ENV_PATH)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-5')
OLLAMA_VISION_MODEL = os.environ.get('OLLAMA_VISION_MODEL', '')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434').rstrip('/')
PORT = int(os.environ.get('PORT', '8002'))

_local = threading.local()


def get_conn():
    conn = getattr(_local, 'conn', None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            'CREATE TABLE IF NOT EXISTS docs('
            'path TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at INTEGER)'
        )
        conn.commit()
        _local.conn = conn
    return conn


def doc_get(path):
    row = get_conn().execute('SELECT data FROM docs WHERE path=?', (path,)).fetchone()
    if row is None:
        return {'exists': False, 'data': None}
    return {'exists': True, 'data': json.loads(row[0])}


def doc_set(path, data):
    conn = get_conn()
    conn.execute(
        'INSERT OR REPLACE INTO docs(path, data, updated_at) VALUES(?,?,?)',
        (path, json.dumps(data), int(time.time() * 1000)),
    )
    conn.commit()


def doc_delete(path):
    conn = get_conn()
    conn.execute('DELETE FROM docs WHERE path=?', (path,))
    conn.commit()


def collection_list(prefix):
    rows = get_conn().execute(
        'SELECT path, data FROM docs WHERE path LIKE ? ESCAPE ?',
        (prefix.replace('%', r'\%').replace('_', r'\_') + '%', '\\'),
    ).fetchall()
    return [{'id': p[len(prefix):], 'data': json.loads(d)} for p, d in rows]


def call_anthropic(prompt, images):
    if not ANTHROPIC_API_KEY:
        return {'error': 'No ANTHROPIC_API_KEY configured on the server.', 'code': 'not_granted'}
    content = [{'type': 'text', 'text': prompt}]
    for img in images or []:
        m = re.match(r'^data:(image/[\w.+-]+);base64,(.*)$', img, re.S)
        if not m:
            continue
        content.append({
            'type': 'image',
            'source': {'type': 'base64', 'media_type': m.group(1), 'data': m.group(2)},
        })
    body = json.dumps({
        'model': ANTHROPIC_MODEL,
        'max_tokens': 8192,
        'messages': [{'role': 'user', 'content': content}],
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=body,
        method='POST',
        headers={
            'content-type': 'application/json',
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {'error': 'rate limited', 'code': 'rate_limited', 'status': 429}
        try:
            detail = json.loads(e.read())
        except Exception:
            detail = {}
        return {'error': json.dumps(detail) or str(e), 'code': 'unknown'}
    except Exception as e:
        return {'error': str(e), 'code': 'unknown'}

    text = ''.join(b.get('text', '') for b in out.get('content', []) if b.get('type') == 'text')
    return parse_json_reply(text)


def parse_json_reply(text):
    text = text.strip()
    if not text:
        return {'error': 'empty completion', 'code': 'empty_completion'}
    text = re.sub(r'^```(?:json)?\s*|\s*```\s*$', '', text)
    try:
        parsed = json.loads(text)
    except Exception:
        return {'error': 'invalid json', 'code': 'invalid_json'}
    return {'result': parsed}


def call_ollama(prompt, images):
    """Send a prompt plus photos to a local Ollama vision model."""
    b64 = []
    for img in images or []:
        m = re.match(r'^data:image/[\w.+-]+;base64,(.*)$', img, re.S)
        if m:
            b64.append(m.group(1))
    if not b64:
        return {'error': 'no readable images', 'code': 'image_rejected'}
    body = json.dumps({
        'model': OLLAMA_VISION_MODEL,
        'stream': False,
        'think': False,
        'format': 'json',
        'messages': [{'role': 'user', 'content': prompt, 'images': b64}],
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL + '/api/chat',
        data=body,
        method='POST',
        headers={'content-type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            out = json.loads(resp.read())
    except Exception as e:
        return {'error': 'Ollama request failed: %s' % e, 'code': 'unknown'}
    return parse_json_reply((out.get('message') or {}).get('content', ''))


def call_ai(prompt, images):
    if images and OLLAMA_VISION_MODEL:
        return call_ollama(prompt, images)
    return call_anthropic(prompt, images)


# ---------- recipe import from a web page ----------

PAGE_MAX_BYTES = 4 * 1024 * 1024
PAGE_TEXT_CHARS = 30000
FETCH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/130.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
}


def public_host(host):
    """True when every address the host resolves to is on the public internet,
    so a pasted link can't make the server poke at the home network."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        if not ip.is_global:
            return False
    return bool(infos)


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urlparse(newurl)
        if u.scheme not in ('http', 'https') or u.port not in (None, 80, 443) \
                or not public_host(u.hostname or ''):
            raise urllib.error.URLError('redirected to a non-public address')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PageReader(HTMLParser):
    """Collects JSON-LD blocks, a few meta tags and the visible text of a page."""
    SKIP = {'script', 'style', 'noscript', 'svg', 'nav', 'footer', 'header', 'form', 'iframe'}
    BLOCK = {'p', 'div', 'li', 'br', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.jsonld, self.meta, self.title = [], {}, ''
        self._text, self._skip, self._ld, self._in_title = [], 0, None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and (a.get('type') or '').lower() == 'application/ld+json':
            self._ld = []
        elif tag == 'meta':
            key = (a.get('property') or a.get('name') or '').lower()
            if key in ('og:site_name', 'og:title', 'author') and a.get('content'):
                self.meta.setdefault(key, a['content'])
        elif tag == 'title':
            self._in_title = True
        if tag in self.SKIP:
            self._skip += 1
        elif tag in self.BLOCK:
            self._text.append('\n')

    def handle_endtag(self, tag):
        if tag == 'script' and self._ld is not None:
            self.jsonld.append(''.join(self._ld))
            self._ld = None
        if tag == 'title':
            self._in_title = False
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag in self.BLOCK:
            self._text.append('\n')

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
        elif self._in_title:
            self.title += data
        elif not self._skip:
            self._text.append(data)

    def text(self):
        t = re.sub(r'[ \t\r\f\v]+', ' ', ''.join(self._text))
        return re.sub(r'\s*\n\s*', '\n', t).strip()


def find_recipe_ld(node):
    """Depth-first search of parsed JSON-LD for a schema.org Recipe."""
    if isinstance(node, list):
        for x in node:
            found = find_recipe_ld(x)
            if found:
                return found
    elif isinstance(node, dict):
        types = node.get('@type')
        types = types if isinstance(types, list) else [types]
        # Matches "Recipe", "schema:Recipe" and "http://schema.org/Recipe".
        if any(re.split(r'[/:]', str(t))[-1] == 'Recipe' for t in types):
            return node
        for key in ('@graph', 'mainEntity', 'mainEntityOfPage'):
            found = find_recipe_ld(node.get(key))
            if found:
                return found
    return None


def drop_media(node):
    if isinstance(node, list):
        return [drop_media(x) for x in node]
    if isinstance(node, dict):
        return {k: drop_media(v) for k, v in node.items()
                if k not in ('image', 'video', 'thumbnailUrl', 'url', '@id')}
    return node


def trim_recipe_ld(r):
    """Keep only the fields that describe the recipe itself (drops images,
    ratings, video blobs and the like that just eat prompt space)."""
    keep = ('name', 'description', 'author', 'publisher', 'recipeYield', 'prepTime',
            'cookTime', 'totalTime', 'recipeIngredient', 'recipeInstructions',
            'recipeCategory', 'recipeCuisine', 'nutrition')
    out = {k: drop_media(r[k]) for k in keep if r.get(k)}
    for k in ('author', 'publisher'):
        v = out.get(k)
        if isinstance(v, list):
            v = v[0] if v else None
        if isinstance(v, dict):
            v = v.get('name')
        if v:
            out[k] = str(v)
        else:
            out.pop(k, None)
    return out


def fetch_recipe_page(url):
    url = (url or '').strip()
    u = urlparse(url)
    try:
        port = u.port
    except ValueError:
        port = -1
    if u.scheme not in ('http', 'https') or not u.hostname or port not in (None, 80, 443):
        return {'error': 'That doesn\'t look like a web link.', 'code': 'bad_url'}
    if not public_host(u.hostname):
        return {'error': 'That link points somewhere the server won\'t fetch.', 'code': 'bad_url'}
    # No proxies: an http_proxy in the environment would sidestep the address check.
    # Known gap: the host is resolved again on connect, so DNS rebinding could
    # still reach a private address. Accepted for a home-network app.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), PublicRedirects)
    req = urllib.request.Request(url, headers=FETCH_HEADERS)
    try:
        with opener.open(req, timeout=20) as resp:
            final_url = resp.geturl()
            ctype = resp.headers.get_content_type()
            charset = resp.headers.get_content_charset() or 'utf-8'
            encoding = (resp.headers.get('Content-Encoding') or '').lower()
            raw = resp.read(PAGE_MAX_BYTES)
    except urllib.error.HTTPError as e:
        return {'error': 'The site answered with an error (%s); it may block '
                         'automated readers.' % e.code,
                'code': 'fetch_failed'}
    except Exception as e:
        return {'error': 'Couldn\'t load that page: %s' % e, 'code': 'fetch_failed'}

    if not (ctype.startswith('text/') or ctype == 'application/xhtml+xml'):
        return {'error': 'That link isn\'t a web page (%s).' % ctype, 'code': 'fetch_failed'}
    if encoding in ('gzip', 'deflate'):
        # wbits 47 auto-detects gzip or zlib headers; -15 is raw deflate.
        for wbits in (47, -15):
            try:
                raw = zlib.decompressobj(wbits).decompress(raw, PAGE_MAX_BYTES * 4)
                break
            except zlib.error:
                continue
        else:
            return {'error': 'That page came back in a form the server can\'t read.', 'code': 'fetch_failed'}
    elif encoding not in ('', 'identity'):
        return {'error': 'That page came back in a form the server can\'t read.', 'code': 'fetch_failed'}

    try:
        page = raw.decode(charset, errors='replace')
    except LookupError:
        page = raw.decode('utf-8', errors='replace')
    reader = PageReader()
    try:
        reader.feed(page)
        reader.close()
    except Exception:
        pass
    recipe = None
    for block in reader.jsonld:
        try:
            recipe = find_recipe_ld(json.loads(block, strict=False))
        except Exception:
            continue
        if recipe:
            recipe = trim_recipe_ld(recipe)
            # A runaway structured block isn't worth the prompt; use the page text.
            if len(json.dumps(recipe)) > PAGE_TEXT_CHARS:
                recipe = None
            break
    site = reader.meta.get('og:site_name') or re.sub(r'^www\.', '', urlparse(final_url).hostname or '')
    return {'result': {
        'url': final_url,
        'site': site,
        'title': (reader.meta.get('og:title') or reader.title).strip(),
        'author': reader.meta.get('author', ''),
        'recipe': recipe,
        # The page text is only needed when there's no structured recipe.
        'text': '' if recipe else reader.text()[:PAGE_TEXT_CHARS],
    }}


class Handler(BaseHTTPRequestHandler):
    server_version = 'MealPlan/1.0'

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0) or 0)
        raw = self.rfile.read(length) if length else b''
        return json.loads(raw) if raw else {}

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path in ('/', '/dinnertable.html'):
            self._serve_html()
        elif parsed.path in STATIC_FILES:
            self._serve_static(*STATIC_FILES[parsed.path])
        elif parsed.path == '/api/doc':
            self._send_json(doc_get(unquote(qs.get('path', [''])[0])))
        elif parsed.path == '/api/collection':
            self._send_json(collection_list(unquote(qs.get('prefix', [''])[0])))
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == '/api/doc':
            path = unquote(qs.get('path', [''])[0])
            doc_set(path, self._read_json())
            self._send_json({'ok': True})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == '/api/collection':
            prefix = unquote(qs.get('prefix', [''])[0])
            new_id = uuid.uuid4().hex[:12]
            doc_set(prefix + new_id, self._read_json())
            self._send_json({'id': new_id})
        elif parsed.path == '/api/ai':
            body = self._read_json()
            result = call_ai(body.get('prompt', ''), body.get('images'))
            status = result.pop('status', 200)
            self._send_json(result, status)
        elif parsed.path == '/api/fetch-page':
            self._send_json(fetch_recipe_page(self._read_json().get('url')))
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == '/api/doc':
            doc_delete(unquote(qs.get('path', [''])[0]))
            self._send_json({'ok': True})
        else:
            self.send_error(404)

    def _serve_html(self):
        with open(HTML_PATH, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, filename, content_type):
        try:
            with open(os.path.join(STATIC_DIR, filename), 'rb') as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(body)


def main():
    if OLLAMA_VISION_MODEL:
        print(f'Photo scans use Ollama model {OLLAMA_VISION_MODEL} at {OLLAMA_URL}', file=sys.stderr)
    if not ANTHROPIC_API_KEY:
        print(
            'Warning: ANTHROPIC_API_KEY is not set -- AI features (plan my week, '
            'recipe ideas, remix, fridge scan) will show an error until you export it.',
            file=sys.stderr,
        )
    get_conn()  # create the DB file / table up front
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Our Dinner Table running on http://0.0.0.0:{PORT}  (db: {DB_PATH})')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
