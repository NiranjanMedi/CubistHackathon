# Lightning Mode UI Toggle — Implementation Report

## Summary

Added a "⚡ Frolicking Lightning" toggle button to `index.html`. When active, all API requests include `mode: "lightning"`, signalling the server to enable the opening book and noise. The button has distinct on/off visual states using a dedicated CSS class.

---

## Files Changed

### `index.html`

**CSS variables and classes added**:

```css
:root {
  --lightning: #f0c030;
}

button.lightning     { background: var(--lightning); color: #1a1a18;
                       border-color: var(--lightning); font-weight: 500; }
button.lightning-off { border-color: var(--lightning); color: var(--lightning); }
button.lightning:hover     { opacity: 0.85; }
```

**Button added** in the button row:

```html
<button id="lightningBtn" class="lightning-off" onclick="toggleLightning()">
  ⚡ Frolicking Lightning
</button>
```

**State variable and toggle function**:

```javascript
let lightning = false;

function toggleLightning() {
  lightning = !lightning;
  const btn = document.getElementById('lightningBtn');
  btn.className = lightning ? 'lightning' : 'lightning-off';
}
```

**`sendMove` updated**:

```javascript
async function sendMove(uci) {
  const data = await api('/move', { move: uci, mode: lightning ? 'lightning' : 'normal' });
  if (data) { state = data; render(); }
}
```

**`engineStep` updated**:

```javascript
async function engineStep() {
  const data = await api('/engine_move', { mode: lightning ? 'lightning' : 'normal' });
  if (data) { state = data; render(); }
}
```

---

## Design Notes

**Visual design**: amber/gold (`#f0c030`) distinguishes the lightning button from the green accent buttons and red danger buttons already in the palette. Off-state uses outline-only to signal it is a toggle, not a primary action.

**Mode string**: `"lightning"` is checked by exact string comparison on the server (`data.get("mode") == "lightning"`). Any other value — including `"normal"` — leaves the engine in deterministic mode.

**No game logic change**: toggling lightning mid-game is safe. The mode is read fresh on each API call, so it takes effect from the next move onward.
