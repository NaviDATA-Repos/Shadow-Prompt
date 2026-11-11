// Shadow Prompt - background service worker (FAIL-CLOSED version)
// Differences from the original: every failure (rules not loaded, Ollama unreachable,
// timeout, empty/malformed/invalid output) is reported to the content script as
// { success: false, reason }, never as "original text". The content script then blocks submission.

const aiWebsite = 'http://localhost:11434/v1/chat/completions';
const MODEL = 'deepseek-r1:8b'; // or llama3:8b
const TIMEOUT_MS = 15000;       // longest latency observed in the evaluation was about 12.3 s

let rulesCache = null;

async function loadRules() {
  if (rulesCache) return rulesCache;
  const url = chrome.runtime.getURL('validated_policies.json');
  const response = await fetch(url);
  if (!response.ok) throw new Error('rules_unavailable');
  const data = await response.json();
  if (!Array.isArray(data.regole) || data.regole.length === 0) throw new Error('rules_unavailable');
  rulesCache = data.regole;
  return rulesCache;
}

function buildRulesList(rules) {
  const byCategory = {};
  for (const rule of rules) {
    if (!byCategory[rule.category]) byCategory[rule.category] = [];
    byCategory[rule.category].push(rule);
  }
  const lines = [];
  for (const [category, items] of Object.entries(byCategory)) {
    lines.push(`[${category.toUpperCase()}]`);
    for (const item of items) lines.push(`- ${item.data_type.toUpperCase()}: ${item.description}`);
  }
  return lines.join('\n');
}

class MaskingError extends Error {
  constructor(reason) { super(reason); this.reason = reason; }
}

async function hidePII(userText) {
  const start = Date.now();

  let rules;
  try { rules = await loadRules(); } catch (e) { throw new MaskingError('rules_unavailable'); }
  const rulesList = buildRulesList(rules);

  const instructions = `You are a sensitive data detection system. Replace ALL sensitive information with *** in the text below. Return ONLY the modified text with NO explanations.

Replace these with ***:
${rulesList}

IMPORTANT RULES:
1. Replace COMPLETE sensitive data with *** (not partial)
2. If no sensitive data found, return the original text EXACTLY as given
3. DO NOT add explanations like "no data detected" or "modified text:"
4. Return ONLY the text with sensitive data replaced by ***

Text to analyze: ${userText}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let data;
  try {
    const response = await fetch(aiWebsite, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'user', content: instructions }],
        think: false,
        stream: false,
        temperature: 0,
        max_tokens: 1000
      })
    });
    if (!response.ok) throw new MaskingError('llm_http_error');
    data = await response.json();
  } catch (e) {
    if (e instanceof MaskingError) throw e;
    if (e && e.name === 'AbortError') throw new MaskingError('llm_timeout');
    throw new MaskingError('llm_unavailable');   // connection refused, network error, invalid JSON
  } finally {
    clearTimeout(timer);
  }

  console.log('Ollama response time:', Date.now() - start, 'ms');

  const aiAnswer = data?.choices?.[0]?.message?.content?.trim();
  if (!aiAnswer) throw new MaskingError('invalid_output');            // empty or malformed
  if (aiAnswer.includes('Modified text:') ||
      aiAnswer.includes('No sensitive') ||
      aiAnswer.includes('detected')) {
    throw new MaskingError('invalid_output');                          // explanation instead of text
  }
  return aiAnswer;
}

chrome.runtime.onMessage.addListener(function (message, sender, sendReply) {
  if (message.action === 'hidePII') {
    hidePII(message.text)
      .then(function (hiddenText) { sendReply({ success: true, hiddenText: hiddenText }); })
      .catch(function (err) {
        console.warn('Masking failed:', err && err.reason ? err.reason : err);
        sendReply({ success: false, reason: (err && err.reason) || 'unknown' });
      });
    return true; // keep the channel open for the async reply
  }
});
