// Shadow Prompt - content script (FAIL-CLOSED version)
// A prompt can only be submitted when the text currently in the box has been successfully
// processed by the background script. Otherwise the submit action is blocked and a message is shown.

const timers = new WeakMap();
const state = new WeakMap();   // textBox -> { okText: string|null, pending: Promise|null }
let lastBox = null;            // the monitored box the user typed in last

function checkTextBox(el) {
  const textTypes = ['text', 'email', 'search', 'tel', 'url', 'password', ''];
  if (el.tagName === 'INPUT') return textTypes.includes((el.type || '').toLowerCase());
  return el.tagName === 'TEXTAREA' || el.contentEditable === 'true';
}

function getText(textBox) {
  return textBox.contentEditable === 'true' ? textBox.textContent : textBox.value;
}

function giveBack(textBox, newText) {
  if (textBox.contentEditable === 'true') textBox.textContent = newText;
  else textBox.value = newText;
}

function getState(box) {
  if (!state.has(box)) state.set(box, { okText: null, pending: null });
  return state.get(box);
}

// ---- user-visible message ------------------------------------------------
function showBanner(text, kind) {
  let b = document.getElementById('shadowprompt-banner');
  if (!b) {
    b = document.createElement('div');
    b.id = 'shadowprompt-banner';
    b.style.cssText = 'position:fixed;bottom:16px;right:16px;z-index:2147483647;max-width:340px;' +
      'padding:10px 14px;border-radius:8px;font:14px/1.3 sans-serif;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.3)';
    document.documentElement.appendChild(b);
  }
  b.textContent = text;
  b.style.background = kind === 'error' ? '#b00020' : kind === 'ok' ? '#1b6e2d' : '#444';
  b.dataset.kind = kind;
}

// ---- masking request -----------------------------------------------------
// Resolves true when the text in the box is safe to submit, false otherwise.
function ensureChecked(box) {
  const st = getState(box);
  const text = getText(box);
  if (!text || text.length < 3) return Promise.resolve(true);        // nothing to protect (same rule as before)
  if (st.okText === text) return Promise.resolve(true);              // already checked
  if (st.pending && st.pendingText === text) return st.pending;      // check in progress for this text

  st.pendingText = text;
  st.pending = chrome.runtime.sendMessage({ action: 'hidePII', text: text })
    .then(function (response) {
      st.pending = null;
      if (!response || !response.success) {
        st.okText = null;
        showBanner('Sensitive-data protection is unavailable. Submission has been blocked.', 'error');
        return false;
      }
      if (getText(box) !== text) return false;                       // user kept typing: result is stale
      giveBack(box, response.hiddenText);
      st.okText = response.hiddenText;
      showBanner('Prompt checked. You can send it.', 'ok');
      return true;
    })
    .catch(function () {
      st.pending = null;
      st.okText = null;
      showBanner('Sensitive-data protection is unavailable. Submission has been blocked.', 'error');
      return false;
    });
  return st.pending;
}

// ---- typing (debounced check, as in the original) -------------------------
function userIsTyping(event) {
  const box = event.target;
  if (!checkTextBox(box)) return;
  lastBox = box;
  getState(box).okText = (getText(box) === getState(box).okText) ? getState(box).okText : null;
  clearTimeout(timers.get(box));
  timers.set(box, setTimeout(function () { ensureChecked(box); }, 1000));
}
document.addEventListener('input', userIsTyping);

// ---- blocking the submit action -------------------------------------------
function needsCheck() {
  if (!lastBox || !document.contains(lastBox)) return false;
  const text = getText(lastBox);
  if (!text || text.length < 3) return false;
  return getState(lastBox).okText !== text;
}

function blockAndCheck(event) {
  event.preventDefault();
  event.stopImmediatePropagation();
  showBanner('Checking the prompt for sensitive data...', 'info');
  ensureChecked(lastBox);       // outcome is shown in the banner; the user submits again afterwards
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && checkTextBox(e.target) && needsCheck()) blockAndCheck(e);
}, true);

document.addEventListener('click', function (e) {
  const el = e.target.closest && e.target.closest('button, [role="button"], input[type="submit"]');
  if (el && needsCheck()) blockAndCheck(e);
}, true);

document.addEventListener('submit', function (e) {
  if (needsCheck()) blockAndCheck(e);
}, true);
