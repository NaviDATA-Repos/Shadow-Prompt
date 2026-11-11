"""
Esempi di Configurazione per Diverse API LLM
"""

# ============================================================================
# OPENAI (ChatGPT)
# ============================================================================
openai_config = {
    'url': 'https://api.openai.com/v1/chat/completions',
    'api_key': 'sk-YOUR_OPENAI_KEY',
    'model': 'gpt-4'  # o 'gpt-3.5-turbo'
}

# ============================================================================
# ANTHROPIC (Claude)
# ============================================================================
anthropic_config = {
    'url': 'https://api.anthropic.com/v1/messages',
    'api_key': 'sk-ant-YOUR_ANTHROPIC_KEY',
    'model': 'claude-3-5-sonnet-20241022',
    'headers': {
        'anthropic-version': '2023-06-01'
    }
}

# ============================================================================
# AZURE OPENAI
# ============================================================================
azure_config = {
    'url': 'https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT/chat/completions?api-version=2024-02-15-preview',
    'api_key': 'YOUR_AZURE_KEY',
    'model': 'gpt-4',
    'headers': {
        'api-key': 'YOUR_AZURE_KEY'  # Azure usa 'api-key' invece di Authorization
    }
}

# ============================================================================
# GOOGLE (Gemini)
# ============================================================================
google_config = {
    'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
    'api_key': 'YOUR_GOOGLE_API_KEY',
    'model': 'gemini-pro'
}

# ============================================================================
# HUGGING FACE
# ============================================================================
huggingface_config = {
    'url': 'https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2',
    'api_key': 'hf_YOUR_HUGGINGFACE_TOKEN',
    'model': 'mistralai/Mistral-7B-Instruct-v0.2'
}

# ============================================================================
# OLLAMA (locale)
# ============================================================================
ollama_config = {
    'url': 'http://localhost:11434/api/chat',
    'model': 'llama2'
    # Nessuna API key necessaria per Ollama locale
}

# ============================================================================
# LM STUDIO (locale)
# ============================================================================
lmstudio_config = {
    'url': 'http://localhost:1234/v1/chat/completions',
    'model': 'local-model'
    # Nessuna API key necessaria
}

# ============================================================================
# OPENROUTER (aggregatore)
# ============================================================================
openrouter_config = {
    'url': 'https://openrouter.ai/api/v1/chat/completions',
    'api_key': 'YOUR_OPENROUTER_KEY',
    'model': 'anthropic/claude-3-sonnet'  # Supporta molti modelli
}

# ============================================================================
# GROQ (veloce)
# ============================================================================
groq_config = {
    'url': 'https://api.groq.com/openai/v1/chat/completions',
    'api_key': 'gsk_YOUR_GROQ_KEY',
    'model': 'mixtral-8x7b-32768'  # o 'llama2-70b-4096'
}

# ============================================================================
# TOGETHER AI
# ============================================================================
together_config = {
    'url': 'https://api.together.xyz/v1/chat/completions',
    'api_key': 'YOUR_TOGETHER_KEY',
    'model': 'mistralai/Mixtral-8x7B-Instruct-v0.1'
}

# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

"""
from simple_rag import SimpleRAGExtractor

# Scegli la configurazione
config = ollama_config  # Usa Ollama (locale) di default

# Crea estrattore
extractor = SimpleRAGExtractor(api_config=config)

# Estrai regole da testo
policy_text = "..."
rules = extractor.extract_rules(policy_text)

# Esporta JSON
extractor.export_to_json('output.json')
"""

# ============================================================================
# NOTE IMPORTANTI
# ============================================================================

"""
1. OPENAI / AZURE OPENAI
   - Formato standard OpenAI chat completions
   - Supportano function calling
   - Buona qualità, costo medio

2. ANTHROPIC (Claude)
   - Richiede header 'anthropic-version'
   - Eccellente per task analitici
   - Costo leggermente superiore

3. OLLAMA / LM STUDIO
   - Esecuzione LOCALE, privacy totale
   - Nessun costo API
   - Richiede GPU per prestazioni ottimali

4. GROQ
   - Estremamente veloce (inferenza hardware dedicato)
   - Costo competitivo
   - Ottimo per produzione

5. OPENROUTER
   - Accesso a 100+ modelli con una sola API key
   - Comodo per testare diversi modelli
   - Pricing variabile per modello

RACCOMANDAZIONI:
- Sviluppo/Test: Ollama (locale, gratis)
- Produzione qualità: Claude o GPT-4
- Produzione velocità: Groq
- Produzione economica: GPT-3.5-turbo
"""
