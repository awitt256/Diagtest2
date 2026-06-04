// This script displays the most recently pressed key and updates in real-time.
// Press ESC to exit.

// Works in Node.js. If you want Python or another language let me know.

const readline = require('readline');

readline.emitKeypressEvents(process.stdin);

if (process.stdin.isTTY) {
  process.stdin.setRawMode(true);
}

console.clear();
console.log('Press any key. Press ESC to exit.');
console.log('-------------------------------');
console.log('');

const history = [];

process.stdin.on('keypress', (str, key) => {
  if (key && key.sequence === '\u001b') {
    // ESC key pressed
    console.log('\nExiting...');
    process.exit();
  }

  // Build a list of modifiers + main key
  const parts = [];

  if (key && key.ctrl) {
    parts.push('Ctrl');
  }
  if (key && key.meta) {
    // On Windows this is usually the Windows key
    parts.push('Win');
  }
  if (key && key.alt) {
    parts.push('Alt');
  }
  if (key && key.shift) {
    parts.push('Shift');
  }

  // Main key name (letters, numbers, function keys, etc.)
  const mainName = key && key.name ? key.name : str;
  if (mainName) {
    parts.push(mainName);
  }

  // Note: CapsLock usually isn't exposed directly to terminals,
  // but if the terminal sends a name for it, we'll show it.
  const combo = parts.join(' + ') || '(unknown)';

  history.push(combo);

  // Redraw the screen so we always show:
  // - header
  // - last key pressed
  // - full history of keys
  console.clear();
  console.log('Press any key. Press ESC to exit.');
  console.log('-------------------------------');
  console.log(`Last key pressed: ${combo}`);
  console.log('');
  console.log('History:');
  history.forEach((item, index) => {
    console.log(`${index + 1}. ${item}`);
  });
});