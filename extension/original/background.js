// LLM url: Usiamo l'endpoint locale di Ollama compatibile con OpenAI
const aiWebsite = 'http://localhost:11434/v1/chat/completions';

// -------------------------------------------------------
// CARICAMENTO REGOLE DA JSON
// -------------------------------------------------------

// Fix #5: Cache delle regole per evitare ricaricamento ad ogni chiamata
let rulesCache = null;

// Carica le regole dal file regole_estratte.json incluso nell'estensione
// Fix #4: aggiunto try/catch per gestire errori di rete/parsing
async function loadRules() {
  if (rulesCache) return rulesCache;
  try {
    const url = chrome.runtime.getURL('validated_policies.json');
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to load rules: ' + response.status);
    const data = await response.json();
    rulesCache = data.regole;
    return rulesCache;
  } catch (e) {
    console.error('Errore caricamento regole:', e);
    return []; // fallback graceful: nessuna regola, testo non modificato
  }
}

// Converte le regole JSON in testo leggibile per il prompt AI
// Raggruppa per categoria e aggiunge data_type e descrizione
function buildRulesList(rules) {
  const byCategory = {};
  for (const rule of rules) {
    if (!byCategory[rule.category]) {
      byCategory[rule.category] = [];
    }
    byCategory[rule.category].push(rule);
  }

  const lines = [];
  for (const [category, items] of Object.entries(byCategory)) {
    lines.push(`[${category.toUpperCase()}]`);
    for (const item of items) {
      lines.push(`- ${item.data_type.toUpperCase()}: ${item.description}`);
    }
  }
  return lines.join('\n');
}

// -------------------------------------------------------
// FUNZIONE PRINCIPALE: NASCONDI DATI SENSIBILI
// -------------------------------------------------------

// ask AI to hide sensitive data using rules loaded from JSON
async function hidePII(userText) {
  // start time
  var start = Date.now();

  // load rules dynamically from JSON file (cached after first load)
  const rules = await loadRules();
  const rulesList = buildRulesList(rules);

  // build prompt using the JSON rules (no more hardcoded list)
  const instructions = `You are a sensitive data detection system. Replace ALL sensitive information with *** in the text below. Return ONLY the modified text with NO explanations.

Replace these with ***:
${rulesList}

IMPORTANT RULES:
1. Replace COMPLETE sensitive data with *** (not partial)
2. If no sensitive data found, return the original text EXACTLY as given
3. DO NOT add explanations like "no data detected" or "modified text:"
4. Return ONLY the text with sensitive data replaced by ***

Text to analyze: ${userText}`;

  // send message to local AI
  return fetch(aiWebsite, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'deepseek-r1:8b', // Puoi cambiarlo con mistral, phi3 o il modello che preferisci usare: llama3:8b, deepseek-r1:8b, qwen3:8b
      messages: [{
        role: 'user',
        content: instructions
      }],
      think: false,
      stream: false,
      temperature: 0, // Manteniamo la temperatura bassa per evitare risposte creative
      max_tokens: 1000
    })
  })
  .then(function(response) {
    return response.json();
  })
  .then(function(data) {
    var time = Date.now() - start;
    console.log('Tempo di risposta Ollama:', time, 'ms');

    // Fix #8: accesso sicuro a data.choices per evitare crash su risposta malformata
    const aiAnswer = data?.choices?.[0]?.message?.content?.trim();
    if (!aiAnswer) {
      console.warn('Risposta AI vuota o malformata, restituisco testo originale.');
      return userText;
    }

    // if AI gives explanations, just return original text
    if (aiAnswer.includes('Modified text:') ||
        aiAnswer.includes('No sensitive') ||
        aiAnswer.includes('detected')) {
      return userText;
    }

    return aiAnswer;
  })
  .catch(function(error) {
    console.log('Ollama error:', error); // Potrebbe fallire se Ollama e' spento
    return userText;
  });
}

// -------------------------------------------------------
// LISTENER MESSAGGI DAL CONTENT SCRIPT
// -------------------------------------------------------

// listen when webpage asks for help
chrome.runtime.onMessage.addListener(function(message, sender, sendReply) {
  if (message.action === 'hidePII') {
    hidePII(message.text)
      .then(function(hiddenText) {
        sendReply({ success: true, hiddenText: hiddenText });
      })
      .catch(function() {
        sendReply({ success: false });
      });
    return true; // keep connection open
  }
});
