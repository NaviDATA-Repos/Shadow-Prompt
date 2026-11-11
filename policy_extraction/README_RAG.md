# Sistema RAG per Estrazione Regole da PDF

Sistema semplice e modulare che usa un'architettura RAG (Retrieval-Augmented Generation) per estrarre regole atomiche da policy aziendali in PDF.

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────────────┐
│                     INPUT PDF/TEXT                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1: RETRIEVAL                                      │
│  • Estrae contesto rilevante (frasi con regole)         │
│  • Filtra sezioni importanti                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: GENERATION (LLM API)                           │
│  • Invia contesto + knowledge base all'LLM             │
│  • LLM estrae regole atomiche                           │
│  • Formato JSON strutturato                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: PARSING                                        │
│  • Parse della risposta JSON                            │
│  • Validazione e normalizzazione                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              OUTPUT: regole_rag.json                     │
│  {                                                       │
│    "regole": [                                           │
│      {                                                   │
│        "data_type": "nome",                              │
│        "category": "dati_personali",                     │
│        "severity": "alta",                               │
│        "description": "Nome di persona fisica"           │
│      }                                                   │
│    ]                                                     │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installazione

```bash
pip install requests --break-system-packages
# Opzionale per PDF:
pip install pymupdf --break-system-packages
```

### Uso Base (Modalità Mock)

```python
from simple_rag import SimpleRAGExtractor

# Crea estrattore (modalità mock, senza API)
extractor = SimpleRAGExtractor()

# Testo della policy
policy = """
È vietato condividere nome, cognome, email e password dei dipendenti.
Non divulgare IBAN, fatturato o budget aziendale.
"""

# Estrai regole
rules = extractor.extract_rules(policy)

# Esporta JSON
extractor.export_to_json('output.json')
```

### Uso con LLM API

```python
from simple_rag import SimpleRAGExtractor

# Configura la tua API
api_config = {
    'url': 'https://api.openai.com/v1/chat/completions',
    'api_key': 'sk-YOUR_KEY',
    'model': 'gpt-4'
}

# Crea estrattore con API
extractor = SimpleRAGExtractor(api_config=api_config)

# Estrai da PDF
text = extractor.extract_text_from_pdf('policy.pdf')
rules = extractor.extract_rules(text)

# Salva risultati
extractor.export_to_json('regole.json')
```

## ⚙️ Configurazione API

### OpenAI (GPT-4)

```python
api_config = {
    'url': 'https://api.openai.com/v1/chat/completions',
    'api_key': 'sk-YOUR_OPENAI_KEY',
    'model': 'gpt-4'
}
```

### Anthropic (Claude)

```python
api_config = {
    'url': 'https://api.anthropic.com/v1/messages',
    'api_key': 'sk-ant-YOUR_KEY',
    'model': 'claude-3-5-sonnet-20241022',
    'headers': {
        'anthropic-version': '2023-06-01'
    }
}
```

### Ollama (Locale, Gratis)

```bash
# Installa Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Scarica un modello
ollama pull llama2
```

```python
api_config = {
    'url': 'http://localhost:11434/api/chat',
    'model': 'llama2'
}
```

### Groq (Veloce)

```python
api_config = {
    'url': 'https://api.groq.com/openai/v1/chat/completions',
    'api_key': 'gsk_YOUR_GROQ_KEY',
    'model': 'mixtral-8x7b-32768'
}
```

Vedi `llm_configs.py` per altre configurazioni (Azure, Google, HuggingFace, etc.)

## 📊 Output JSON

```json
{
  "metadata": {
    "total_rules": 35,
    "categories": [
      "dati_personali",
      "dati_finanziari",
      "credenziali",
      "dati_tecnici",
      "dati_aziendali",
      "dati_sanitari"
    ],
    "severities": ["critica", "alta", "media", "bassa"]
  },
  "regole": [
    {
      "data_type": "nome",
      "category": "dati_personali",
      "severity": "alta",
      "description": "Nome di persona fisica"
    },
    {
      "data_type": "iban",
      "category": "dati_finanziari",
      "severity": "critica",
      "description": "Codice IBAN conto corrente"
    }
  ]
}
```

## 🎯 Categorie Supportate

| Categoria | Esempi |
|-----------|--------|
| **dati_personali** | nome, cognome, indirizzo, telefono, email, codice fiscale |
| **dati_finanziari** | IBAN, carta di credito, stipendio, fatturato, bilancio |
| **credenziali** | password, PIN, token, API key, certificato |
| **dati_tecnici** | indirizzo IP, configurazione, vulnerabilità, server |
| **dati_aziendali** | brevetto, segreto industriale, contratto, roadmap |
| **dati_sanitari** | cartella clinica, diagnosi, terapia, farmaco |

## 🔧 Personalizzazione

### Aggiungere Nuove Categorie

```python
extractor = SimpleRAGExtractor()

# Aggiungi categoria personalizzata
extractor.knowledge_base['dati_ricerca'] = [
    'protocollo sperimentale',
    'dati clinici',
    'risultati test'
]

rules = extractor.extract_rules(text)
```

### Modificare il Prompt

Modifica il metodo `extract_rules()` in `simple_rag.py`:

```python
prompt = f"""
TUO PROMPT PERSONALIZZATO

{context}

FORMATO RICHIESTO:
[{{"data_type": "...", "category": "...", ...}}]
"""
```

### Gestire Formati API Diversi

Se la tua API ha un formato diverso, sovrascrivi `call_llm()`:

```python
class CustomRAGExtractor(SimpleRAGExtractor):
    def call_llm(self, prompt):
        # Implementa la tua logica qui
        response = requests.post(...)
        return response.text
```

## 📝 Esempi Pratici

### Esempio 1: Pipeline Completa

```python
# 1. Inizializza
extractor = SimpleRAGExtractor(api_config)

# 2. Estrai da PDF
text = extractor.extract_text_from_pdf('policy_aziendale.pdf')

# 3. Estrai regole
rules = extractor.extract_rules(text)

# 4. Filtra per severità critica
critical = [r for r in rules if r.severity == 'critica']

# 5. Esporta
extractor.export_to_json('regole_critiche.json')
```

### Esempio 2: Validazione Testi

```python
# Carica regole estratte
import json
with open('regole_rag.json') as f:
    data = json.load(f)

# Funzione di validazione
def validate_text(text, rules_data):
    violations = []
    text_lower = text.lower()
    
    for rule in rules_data['regole']:
        if rule['data_type'].replace('_', ' ') in text_lower:
            violations.append(rule)
    
    return violations

# Valida testo
text = "Invia il pagamento su IBAN IT12345..."
violations = validate_text(text, data)

if violations:
    print("⚠️ ATTENZIONE! Il testo contiene dati sensibili:")
    for v in violations:
        print(f"  • {v['data_type']} [{v['severity']}]")
```

### Esempio 3: Batch Processing

```python
import os

# Processa multipli PDF
pdf_folder = './policies/'
all_rules = []

for pdf_file in os.listdir(pdf_folder):
    if pdf_file.endswith('.pdf'):
        print(f"Elaborando {pdf_file}...")
        
        text = extractor.extract_text_from_pdf(
            os.path.join(pdf_folder, pdf_file)
        )
        rules = extractor.extract_rules(text)
        all_rules.extend(rules)

# Rimuovi duplicati
unique_rules = list({r.data_type: r for r in all_rules}.values())

# Esporta
output = {
    'metadata': {'total_rules': len(unique_rules)},
    'regole': [r.to_dict() for r in unique_rules]
}

with open('regole_consolidate.json', 'w') as f:
    json.dump(output, f, indent=2)
```

## 🧪 Testing

### Modalità Mock

Per testare senza API LLM:

```python
# Non passare api_config
extractor = SimpleRAGExtractor()

# Usa analisi basata su keyword
rules = extractor.extract_rules(policy_text)
```

### Con API Reale

```python
# Usa la tua API
extractor = SimpleRAGExtractor(api_config)
rules = extractor.extract_rules(policy_text)
```

## 🔍 Troubleshooting

### Errore: "Connection refused"

Verifica che l'URL API sia corretto e raggiungibile.

### Errore: "Invalid API key"

Controlla che l'API key sia valida e non scaduta.

### PDF non si apre

Installa PyMuPDF: `pip install pymupdf --break-system-packages`

### Risposta LLM non parsabile

Il parsing cerca automaticamente JSON. Se fallisce, controlla il formato della risposta LLM.

## 📊 Performance

| LLM | Velocità | Costo/1K token | Qualità |
|-----|----------|----------------|---------|
| GPT-4 | Media | $0.03 | ⭐⭐⭐⭐⭐ |
| GPT-3.5 | Veloce | $0.002 | ⭐⭐⭐⭐ |
| Claude 3.5 | Media | $0.015 | ⭐⭐⭐⭐⭐ |
| Groq (Mixtral) | Molto veloce | $0.0002 | ⭐⭐⭐⭐ |
| Ollama (locale) | Dipende da GPU | Gratis | ⭐⭐⭐ |

## 🛡️ Sicurezza

- **Privacy**: Usa Ollama per elaborazione locale (zero dati inviati online)
- **API Key**: Non committare API key nel codice (usa variabili ambiente)
- **Validazione**: Il sistema valida sempre l'output LLM prima di usarlo

```python
import os

api_config = {
    'url': 'https://api.openai.com/v1/chat/completions',
    'api_key': os.environ.get('OPENAI_API_KEY'),
    'model': 'gpt-4'
}
```

## 📄 Licenza

Open source - usa liberamente per progetti personali e commerciali.

## 🤝 Contributi

Per miglioramenti o bug report, apri una issue!
