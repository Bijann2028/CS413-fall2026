'use strict';
const $ = id => document.getElementById(id);
let sid = null;
let playing = false;
let busy = false;
let done = false;
let count = 0;
let size = 8;
let stopAtSolution = false;
let requestId = 0;
let playbackGeneration = 0;

async function rpc(method, params) {
  const response = await fetch('/rpc', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', id: ++requestId, method, params})
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const body = await response.json();
  if (body.error) {
    const error = new Error(body.error.message);
    error.code = body.error.code;
    throw error;
  }
  return body.result;
}

function describe(event) {
  if (event.event === 'ready') return 'Ready. Start a new search.';
  if (event.event === 'done') return `Search complete. ${count} solutions.`;
  if (event.event === 'solution') return `Solution ${count}: columns ${event.board.join(', ')}.`;
  const location = `row ${event.row}, column ${event.column}`;
  if (event.event === 'reject') {
    const previous = event.board.findIndex((column, row) =>
      column === event.column || Math.abs(column - event.column) === event.row - row);
    if (previous >= 0) {
      const reason = event.board[previous] === event.column ? 'same column' : 'diagonal';
      return `reject — ${location}: ${reason} conflict with row ${previous}, column ${event.board[previous]}.`;
    }
  }
  if (event.event === 'backtrack') return `backtrack — remove queen at ${location}; resume the next candidate.`;
  return `${event.event} — ${location}`;
}

function render(event = {event: 'ready', board: []}) {
  const board = $('board');
  board.innerHTML = '';
  board.className = event.event;
  board.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const cell = document.createElement('div');
      cell.className = `cell ${(row + column) % 2 ? 'dark' : ''}`;
      const candidate = row === event.row && column === event.column;
      if (candidate) cell.classList.add(event.event);
      if ((event.board || [])[row] === column ||
          (candidate && ['try', 'reject'].includes(event.event))) {
        cell.textContent = '♛';
      }
      board.appendChild(cell);
    }
  }
  if (event.event === 'solution') count++;
  $('count').textContent = count;
  const description = describe(event);
  $('status').textContent = description;
  board.setAttribute('aria-label', `${size} by ${size} queen board. ${description} Placed columns by row: ${(event.board || []).join(', ') || 'none'}.`);
  const item = document.createElement('li');
  item.textContent = description;
  $('log').prepend(item);
  while ($('log').children.length > 12) $('log').lastChild.remove();
}

function pause() {
  // Invalidate any older loop still waiting for its playback timer.
  playbackGeneration++;
  playing = false;
  $('play').textContent = 'Play';
}

async function guarded(action) {
  // Exactly one request may change stream state at a time.
  if (busy) return;
  busy = true;
  for (const id of ['start', 'step', 'next', 'reset']) $(id).disabled = true;
  try {
    await action();
  } catch (error) {
    pause();
    $('status').textContent = `Error: ${error.message}. Use Start to restart.`;
  } finally {
    busy = false;
    for (const id of ['start', 'step', 'next', 'reset']) $(id).disabled = false;
  }
}

async function close() {
  if (!sid) return;
  try {
    await rpc('queens.close', {stream_id: sid});
  } catch (error) {
    if (error.code !== -32001) throw error;
  }
  sid = null;
}

function clearBoard() {
  done = false;
  count = 0;
  size = Number($('size').value);
  $('log').innerHTML = '';
  render();
}

async function start(preservePlayback = false) {
  if (!preservePlayback) pause();
  await close();
  clearBoard();
  sid = (await rpc('queens.open', {size})).stream_id;
  $('status').textContent = 'Stream opened. Step or Play to begin.';
}

async function step() {
  if (!sid) await start(true);
  if (done) return;
  const result = await rpc('queens.next', {stream_id: sid, limit: 1});
  for (const event of result.events) {
    render(event);
    if (event.event === 'solution' && stopAtSolution) pause();
  }
  done = result.done;
  if (done) pause();
}

async function loop() {
  const generation = ++playbackGeneration;
  while (playing && generation === playbackGeneration) {
    await guarded(step);
    await new Promise(resolve => setTimeout(resolve, Number($('speed').value)));
  }
}

$('start').onclick = () => guarded(start);
$('step').onclick = () => {
  pause();
  guarded(step);
};
$('reset').onclick = () => guarded(async () => {
  pause();
  await close();
  clearBoard();
});
$('play').onclick = () => {
  if (playing) {
    pause();
    return;
  }
  if (busy || done) return;
  stopAtSolution = false;
  playing = true;
  $('play').textContent = 'Pause';
  loop();
};
$('next').onclick = () => {
  if (playing || busy || done) return;
  stopAtSolution = true;
  playing = true;
  $('play').textContent = 'Pause';
  loop();
};
render();
