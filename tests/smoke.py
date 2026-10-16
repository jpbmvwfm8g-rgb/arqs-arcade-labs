"""ARQS Arcade Labs headless smoke test (local only; Playwright + Chromium).
Run: python3 tests/smoke.py
Serves the repo on localhost, opens every lab, drives basic input, asserts no JS errors,
and checks game state for the paddle lab (launch, pause, resume, game over, best score).
Also runs each page with localStorage blocked to prove the storage guard."""
import http.server, socketserver, threading, os, sys, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ['index.html', 'paddle-lab.html', 'break-lab.html', 'drop-lab.html', 'snake-lab.html', 'risk-pulse.html', 'cost-estimator.html']
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
handler = functools.partial(Quiet, directory=ROOT)
httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{port}/'
results = []

def check(name, ok, detail=''):
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail else ''))

BLOCK_STORAGE = """Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } });"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    for blocked in (False, True):
        for page_name in PAGES:
            ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
            if blocked: ctx.add_init_script(BLOCK_STORAGE)
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('dialog', lambda d: d.dismiss())
            page.goto(base + page_name)
            page.wait_for_timeout(300)
            if page.locator('canvas').count():
                page.locator('canvas').first.click(force=True)
            for b in page.locator('button').all()[:1]:
                if page_name in ('snake-lab.html',): b.click()
            for k in ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space', 'p', 'p']:
                page.keyboard.press(k); page.wait_for_timeout(40)
            if page_name == 'risk-pulse.html':
                page.get_by_text('Refresh Indicators').click()
            if page_name == 'cost-estimator.html':
                page.get_by_text('Calculate Range').click()
            page.wait_for_timeout(400)
            tag = ' [storage blocked]' if blocked else ''
            check(f'{page_name}{tag}: loads and handles input with no JS errors', not errors, '; '.join(errors)[:300])
            ctx.close()

    # Paddle Lab behaviour
    ctx = browser.new_context(); page = ctx.new_page(); errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base + 'paddle-lab.html'); page.wait_for_timeout(200)
    st = lambda: page.evaluate('({launched: ball.launched, paused, lives, x: ball.x, px: paddle.x, pw: paddle.w, y: ball.y, py: paddle.y})')
    s0 = st()
    check('paddle: ball rests on paddle before launch', (not s0['launched']) and abs(s0['x'] - (s0['px'] + s0['pw'] / 2)) < 1 and s0['y'] < s0['py'])
    page.keyboard.down('ArrowRight'); page.wait_for_timeout(300); page.keyboard.up('ArrowRight')
    s1 = st()
    check('paddle: keyboard moves paddle (and resting ball) before launch', s1['px'] > s0['px'] and abs(s1['x'] - (s1['px'] + s1['pw'] / 2)) < 1)
    page.keyboard.press('Space'); page.wait_for_timeout(100); s2 = st()
    check('paddle: Space launches without pausing', s2['launched'] and not s2['paused'], str(s2))
    page.keyboard.press('Space'); s3 = st()
    check('paddle: Space pauses once in play', s3['paused'])
    page.keyboard.press('p'); s4 = st()
    check('paddle: P resumes', not s4['paused'])
    page.evaluate('score = 4321; lives = 1; ball.y = canvas.height + 50; ball.dy = 5')
    page.wait_for_timeout(200)
    over = page.evaluate("({vis: getComputedStyle(document.getElementById('overlay')).display, score: String(score), best: localStorage.getItem('arqsPaddleBest'), hud: document.getElementById('best').textContent})")
    check('paddle: game over overlay + best score persisted', over['vis'] == 'block' and int(over['score']) >= 4321 and over['best'] == over['score'] == over['hud'], str(over))
    page.click('#overlayBtn'); s5 = st()
    check('paddle: Play Again resets lives and unpauses', s5['lives'] == 3 and not s5['paused'] and not s5['launched'])
    check('paddle: no JS errors during behaviour run', not errors, '; '.join(errors)[:300])
    ctx.close()

    # Snake: rapid opposite turn within one tick must not kill the snake
    ctx = browser.new_context(); page = ctx.new_page()
    page.goto(base + 'snake-lab.html'); page.evaluate('startGame(); clearInterval(gameLoop)')
    page.keyboard.press('ArrowUp'); page.keyboard.press('ArrowLeft')  # Up then Left before a tick
    page.evaluate('update()')
    alive = page.evaluate('running')
    check('snake: buffered turns prevent instant self-reversal', alive)
    ctx.close()
    browser.close()

httpd.shutdown()
print(f"\n{sum(results)} passed, {len(results) - sum(results)} failed")
sys.exit(0 if all(results) else 1)
