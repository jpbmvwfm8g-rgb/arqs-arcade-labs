# arqs-arcade-labs

ARQS Arcade Labs: interactive browser games and labs. Pure HTML5 Canvas and vanilla JS, with no backend, no build step and no third-party scripts. Part of ARQS Software Intelligence Systems.

## Labs (release candidate 1.0.0-rc1)

| Lab | File | Highlights | Best-score key |
|---|---|---|---|
| Paddle Lab | `paddle-lab.html` | Lives, levels, wide/slow power-ups, pause, touch, Web Audio SFX | `arqsPaddleBest` |
| Break Lab | `break-lab.html` | Pause, particles, overlays, keyboard control, improved collision | `arqsBreakBest` |
| Drop Lab | `drop-lab.html` | Next/hold, hard drop, levels, pause, overlays, line-clear effects | `arqsDropBest` |
| Snake Lab (prototype) | `snake-lab.html` | Classic snake, buffered turns, local high score | `snake-high` |
| Risk Pulse | `risk-pulse.html` | History chart, threshold colours, persistence, reset | `risk-pulse` state |
| Cost Estimator | `cost-estimator.html` | Region factor, contingency, saved inputs | saved inputs |

Controls for every lab are on the index page under **How to Play**.

All storage access is guarded, so every lab still runs when `localStorage` is blocked (private mode, sandboxed iframes).

## Tests (local only, no CI minutes)

```sh
node tests/static.test.cjs   # structure, script compile, links, no external scripts/secrets, guarded storage
python3 tests/smoke.py       # headless Chromium: every page with and without storage, Paddle/Snake behaviour
```

The smoke test needs Python Playwright with Chromium installed.

## Provenance

The 1.0.0-rc1 consolidation picks the most advanced version of each lab from the earlier draft branches and PRs (#1 to #6 plus the Grok hourly branches) and fixes the defects listed in the consolidation PR. Production deploy is held for Admiral Ack and SOL approval.

Powered by ARQS Software Intelligence Systems 2026.
