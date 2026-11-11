"""
ESEMPIO PRATICO - Come usare il sistema RAG
Inserisci qui la tua API e il percorso del PDF
"""

from simple_rag import SimpleRAGExtractor

# ============================================================================
# PASSO 1: CONFIGURA LA TUA API LLM
# ============================================================================

# Scegli UNA delle configurazioni qui sotto e rimuovi il commento (#)

# --- OPZIONE 1: OpenAI (GPT) ---
#api_config = {
#    'url': 'https://api.openai.com/v1/chat/completions',
#    'api_key': 'sk-INSERISCI_QUI_LA_TUA_CHIAVE',  # ⚠️ CAMBIA QUESTO!
#    'model': 'gpt-4'  # o 'gpt-3.5-turbo' (più economico)
#}

# --- OPZIONE 2: Anthropic (Claude) ---
# api_config = {
#     'url': 'https://api.anthropic.com/v1/messages',
#     'api_key': 'sk-ant-INSERISCI_QUI_LA_TUA_CHIAVE',  # ⚠️ CAMBIA QUESTO!
#     'model': 'claude-3-5-sonnet-20241022',
#     'headers': {
#         'anthropic-version': '2023-06-01'
#     }
# }

# --- OPZIONE 3: Groq (Veloce e Economico) ---
# api_config= {
#     'url': 'https://api.groq.com/openai/v1/chat/completions',
#     'api_key': 'gsk_YOUR_GROQ_KEY',
#     'model': 'llama2-70b-4096' 
# }

# --- OPZIONE 4: Ollama (Locale, Gratis) ---
# Prima installa Ollama: https://ollama.ai
# Poi: ollama pull llama3.1
api_config = {
    'url': 'http://localhost:11434/api/chat',
    'model': 'llama3.1:latest'
    # Nessuna API key necessaria per Ollama locale
}

# --- OPZIONE 5: Modalità MOCK (per testare senza API) ---
# api_config = None  # Non passa configurazione, usa modalità mock


# ============================================================================
# PASSO 2: INSERISCI IL PERCORSO DEI TUOI PDF
# ============================================================================

# Lista di file PDF da analizzare
pdf_sources = [
    'GDPR.pdf',
    'AI_ACT.pdf'
]

# Opzione D: Usa testo diretto (senza PDF) - Decommenta se necessario
# pdf_sources = []
# testo_diretto = """
# INSERISCI QUI IL TESTO DELLA TUA POLICY
# Es: È vietato condividere nome, cognome, email...
# """


# ============================================================================
# PASSO 3: ESEGUI IL CODICE (non modificare sotto questa linea)
# ============================================================================

def main():
    print("=" * 80)
    print("🔐 ESTRAZIONE REGOLE DA PDF CON RAG")
    print("=" * 80)
    print()
    
    # Crea estrattore con la tua API
    print("⚙️  Inizializzazione sistema...")
    
    if api_config:
        print(f"   API: {api_config['url']}")
        print(f"   Modello: {api_config.get('model', 'default')}")
    else:
        print("   Modalità: MOCK (senza API)")
    
    extractor = SimpleRAGExtractor(api_config=api_config)
    print("   ✅ Sistema pronto\n")
    
    # Estrai testo dai PDF o usa testo diretto
    print("📄 Caricamento documenti...")
    all_extracted_rules = []
    
    try:
        if pdf_sources:
            for current_pdf in pdf_sources:
                print(f"\n📄 Analisi documento: {current_pdf}")
                text = extractor.extract_text_from_pdf(current_pdf)
                if not text:
                    print(f"   ❌ Impossibile leggere il PDF: {current_pdf}")
                    continue
                
                print(f"   ✅ PDF letto: {len(text)} caratteri")
                
                # Estrai regole con RAG per questo documento
                print("   🤖 Estrazione regole con RAG...")
                file_rules = extractor.extract_rules(text)
                all_extracted_rules.extend(file_rules)
                print(f"   ✅ {len(file_rules)} regole trovate in questo file.")
        elif 'testo_diretto' in locals() or 'testo_diretto' in globals():
            # Usa testo diretto
            text = testo_diretto
            print(f"   ✅ Testo diretto caricato: {len(text)} caratteri")
            file_rules = extractor.extract_rules(text)
            all_extracted_rules.extend(file_rules)
        else:
            print("❌ ERRORE: Devi impostare 'pdf_sources' o 'testo_diretto'")
            return
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        return
    
    rules = all_extracted_rules
    
    if not rules:
        print("❌ Nessuna regola estratta complessivamente")
        return
    
    # Mostra risultati
    print("\n" + "=" * 80)
    print("📊 RISULTATI")
    print("=" * 80)
    print()
    
    # Raggruppa per categoria
    from collections import defaultdict
    by_category = defaultdict(list)
    
    for rule in rules:
        by_category[rule.category].append(rule)
    
    # Stampa per categoria
    for category in sorted(by_category.keys()):
        cat_rules = by_category[category]
        print(f"\n📁 {category.upper().replace('_', ' ')} ({len(cat_rules)} regole)")
        print("-" * 80)
        
        for rule in cat_rules:
            severity_icon = {
                'critica': '🔴',
                'alta': '🟠',
                'media': '🟡',
                'bassa': '🟢'
            }.get(rule.severity, '⚪')
            
            print(f"  {severity_icon} {rule.data_type}")
    
    # Esporta JSON
    print("\n" + "=" * 80)
    output_path = 'regole_estratte.json'
    json_data = extractor.export_to_json(output_path)
    
    print(f"\n📈 Statistiche:")
    print(f"   • Regole totali: {len(rules)}")
    print(f"   • Categorie: {len(by_category)}")
    print(f"   • File JSON: {output_path}")
    
    print("\n" + "=" * 80)
    print("✅ COMPLETATO!")
    print("=" * 80)
    print()
    print("📂 Il file JSON è disponibile in:")
    print(f"   {output_path}")
    print()
    print("💡 Puoi usare questo JSON per:")
    print("   • Validare testi prima della pubblicazione")
    print("   • Creare blacklist automatiche")
    print("   • Integrare in sistemi di compliance")
    print()


if __name__ == "__main__":
    # Verifica configurazione
    if api_config and 'INSERISCI_QUI' in api_config.get('api_key', ''):
        print("⚠️  ATTENZIONE!")
        print("=" * 80)
        print()
        print("Devi configurare la tua API key!")
        print()
        print("1. Apri questo file: usa_il_sistema.py")
        print("2. Vai a PASSO 1 e inserisci la tua API key")
        print("3. Sostituisci 'INSERISCI_QUI_LA_TUA_CHIAVE' con la tua chiave")
        print()
        print("Esempio:")
        print("   'api_key': 'sk-proj-abc123...'  # Tua chiave reale")
        print()
        print("=" * 80)
        print()
        print("ALTERNATIVE:")
        print("• Usa Ollama (locale, gratis): https://ollama.ai")
        print("• Usa modalità MOCK: imposta api_config = None")
        print()
    else:
        main()
