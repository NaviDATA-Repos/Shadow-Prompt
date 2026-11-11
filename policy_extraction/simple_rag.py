"""
Sistema RAG Migliorato per Estrazione Regole da PDF
Architettura: Chunking → Retrieval → LLM Generation → Parsing → Dedup → JSON

Miglioramenti rispetto alla versione precedente:
  - Chunking con overlap: elabora l'intero documento a blocchi
  - Retrieval espanso: pattern normativi più completi (GDPR, AI Act)
  - Prompt più efficace: specifico per normativa europea
  - Deduplicazione intelligente per evitare regole doppie tra chunk
  - Batch processing: ogni chunk viene inviato separatamente all'LLM
"""

import json
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import requests


@dataclass
class Rule:
    """Regola atomica estratta"""
    data_type: str
    category: str
    severity: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


class SimpleRAGExtractor:
    """Estrattore RAG con LLM API configurabile e chunking avanzato"""

    # Dimensione di ogni chunk di testo (in caratteri)
    CHUNK_SIZE = 3000
    # Overlap tra chunk consecutivi (evita di perdere regole a cavallo dei chunk)
    CHUNK_OVERLAP = 400

    def __init__(self, api_config: Optional[Dict] = None):
        """
        Args:
            api_config: Configurazione API LLM
                {
                    'url': 'https://api.example.com/v1/chat/completions',
                    'api_key': 'your-api-key',          # opzionale (Ollama non lo richiede)
                    'model': 'llama3.1:latest',
                    'headers': {...}                    # opzionale
                }
        """
        self.api_config = api_config or {}
        self.rules: List[Rule] = []
        self.knowledge_base = self._load_knowledge_base()

    # -------------------------------------------------------------------------
    # Knowledge Base
    # -------------------------------------------------------------------------
    def _load_knowledge_base(self) -> Dict:
        """Knowledge base estesa: categorie GDPR + AI Act"""
        return {
            "dati_personali": [
                "nome", "cognome", "indirizzo", "telefono", "email",
                "codice fiscale", "carta d'identità", "passaporto",
                "data di nascita", "luogo di nascita", "numero documento",
                "residenza", "domicilio", "nazionalità",
            ],
            "dati_finanziari": [
                "IBAN", "carta di credito", "conto corrente", "stipendio",
                "fatturato", "bilancio", "budget", "prezzo",
                "reddito", "patrimonio", "transazione bancaria",
                "dati di pagamento", "numero di conto",
            ],
            "credenziali": [
                "password", "PIN", "token", "API key", "certificato",
                "username", "chiave privata", "chiave di cifratura",
                "credenziali di accesso", "secret", "passphrase",
                "autenticazione a due fattori", "OTP",
            ],
            "dati_tecnici": [
                "indirizzo IP", "configurazione", "vulnerabilità",
                "architettura", "server", "database", "porta",
                "codice sorgente", "algoritmo", "modello AI",
                "dataset di addestramento", "parametri del modello",
                "score di rischio AI", "profilo comportamentale AI",
                "sistema di sorveglianza", "sistema di riconoscimento",
            ],
            "dati_aziendali": [
                "segreto industriale", "brevetto", "strategia",
                "contratto", "cliente", "fornitore", "roadmap",
                "proprietà intellettuale", "know-how", "offerta commerciale",
                "listino prezzi", "piano di sviluppo",
            ],
            "dati_sanitari": [
                "cartella clinica", "diagnosi", "terapia", "farmaco",
                "gruppo sanguigno", "disabilità", "allergie",
                "anamnesi", "referto medico", "prescrizione",
                "dati genetici", "stato di salute", "malattia",
                "ricovero", "cartella sanitaria elettronica",
            ],
            "dati_biometrici": [
                "impronta digitale", "riconoscimento facciale", "template biometrico",
                "voce biometrica", "DNA", "genoma", "iride",
                "geometria della mano", "andatura", "firma dinamica",
                "dati biometrici a scopo identificativo",
            ],
            "dati_giudiziari": [
                "condanna penale", "misura cautelare", "reato", "procedimento giudiziario",
                "sentenza", "dati relativi a reati", "casellario giudiziale",
                "fascicolo penale", "verbale di polizia",
            ],
            "dati_geolocalizzazione": [
                "coordinate GPS", "CAP", "codice postale", "tracciamento posizione",
                "dati di localizzazione", "storico degli spostamenti",
                "geo-fencing", "dati di mobilità",
            ],
            "dati_sensibili_speciali": [
                "orientamento sessuale", "opinioni politiche", "credenze religiose",
                "origine etnica", "appartenenza sindacale",
                "convinzioni filosofiche", "origine razziale",
                "dati sulla vita sessuale",
            ],
            "dati_ai_act": [
                "sistema IA ad alto rischio", "sistema di categorizzazione biometrica",
                "identificazione biometrica remota", "valutazione del rischio",
                "sistema di punteggio sociale", "manipolazione subliminale",
                "sfruttamento delle vulnerabilità", "inferenza delle emozioni",
                "profilazione comportamentale", "deepfake",
                "sistema di raccomandazione", "decision making automatizzato",
            ],
        }

    # -------------------------------------------------------------------------
    # Chunking
    # -------------------------------------------------------------------------
    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Divide il testo in chunk sovrapposti.
        Cerca di spezzare ai confini di paragrafo/frase per non troncare il contesto.
        """
        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.CHUNK_SIZE

            if end < text_len:
                # Tenta di spezzare a un punto fermo/newline vicino alla fine del chunk
                boundary = text.rfind("\n\n", start, end)
                if boundary == -1 or boundary < start + self.CHUNK_SIZE // 2:
                    boundary = text.rfind(". ", start, end)
                if boundary == -1 or boundary < start + self.CHUNK_SIZE // 2:
                    boundary = end
                end = boundary + 1
            else:
                end = text_len

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Avanza con overlap
            start = end - self.CHUNK_OVERLAP

        return chunks

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------
    def retrieve_relevant_context(self, text: str) -> str:
        """
        RETRIEVAL (modalità senza chunking): filtra il testo per sezioni rilevanti.
        Usato solo se si vuole passare un singolo testo già breve.
        Il metodo principale è extract_rules() che usa il chunking.
        """
        rule_patterns = [
            # Divieti espliciti
            r"[^.]*(?:vietato|proibito|non.*condividere|evitare|riservato)[^.]*\.",
            r"[^.]*(?:non deve|non può|è vietato|non è consentito)[^.]*\.",
            r"[^.]*(?:confidenziale|segreto|sensibile|riservato)[^.]*\.",
            # Obblighi normativi GDPR/AI Act
            r"[^.]*(?:deve|devono|è obbligatorio|è necessario|è tenuto a)[^.]*\.",
            r"[^.]*(?:trattamento di dati|dato personale|dati sensibili)[^.]*\.",
            r"[^.]*(?:consenso|autorizzazione|legittimo interesse)[^.]*\.",
            r"[^.]*(?:misure di sicurezza|protezione dei dati|privacy)[^.]*\.",
            r"[^.]*(?:sistema IA|intelligenza artificiale|algoritm)[^.]*\.",
            r"[^.]*(?:rischio|alto rischio|proibito|vietato ai sensi)[^.]*\.",
            r"[^.]*(?:articolo|comma|paragrafo|regolamento)[^.]*\.",
        ]

        relevant: List[str] = []
        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            relevant.extend(matches)

        # Rimuovi duplicati mantenendo l'ordine
        seen: Set[str] = set()
        unique: List[str] = []
        for s in relevant:
            key = s.strip()[:100]
            if key not in seen:
                seen.add(key)
                unique.append(s.strip())

        context = "\n".join(unique)
        return context if context else text[:self.CHUNK_SIZE]

    # -------------------------------------------------------------------------
    # LLM Call
    # -------------------------------------------------------------------------
    def call_llm(self, prompt: str) -> str:
        """Chiama l'API LLM configurata"""
        if not self.api_config:
            return self._mock_llm_response(prompt)

        try:
            url = self.api_config.get("url", "")
            model = self.api_config.get("model", "gpt-4")
            api_key = self.api_config.get("api_key", "")

            is_ollama = "11434" in url and "/api/chat" in url

            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            if "headers" in self.api_config:
                headers.update(self.api_config["headers"])

            payload: Dict = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Sei un esperto giuridico specializzato in GDPR (Regolamento UE 2016/679) "
                            "e AI Act (Regolamento UE 2024/1689). Il tuo compito è estrarre TUTTE le "
                            "regole, divieti, obblighi e restrizioni riguardanti i dati da una sezione "
                            "di testo normativo. Rispondi SEMPRE e SOLO con un array JSON valido."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }

            if is_ollama:
                payload["options"] = {"temperature": 0.1, "num_predict": 3000}
            else:
                payload["temperature"] = 0.1
                payload["max_tokens"] = 3000

            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()

            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            elif "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            elif "content" in result:
                if isinstance(result["content"], list) and len(result["content"]) > 0:
                    return result["content"][0].get("text", str(result["content"]))
                return str(result["content"])
            else:
                return str(result)

        except Exception as e:
            print(f"❌ Errore nella chiamata LLM: {e}")
            return self._mock_llm_response(prompt)

    # -------------------------------------------------------------------------
    # Mock LLM
    # -------------------------------------------------------------------------
    def _mock_llm_response(self, prompt: str) -> str:
        """Risposta mock per testing senza API (keyword matching)"""
        mock_rules = []
        text_lower = prompt.lower()

        for category, keywords in self.knowledge_base.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mock_rules.append({
                        "data_type": keyword.replace(" ", "_").lower(),
                        "category": category,
                        "severity": (
                            "critica" if any(x in text_lower for x in ["vietato", "critico", "proibito"])
                            else "alta" if any(x in text_lower for x in ["riservato", "sensibile", "deve"])
                            else "media"
                        ),
                        "description": f"{keyword.capitalize()} — rilevato nel documento",
                    })

        seen: Set[str] = set()
        unique = []
        for rule in mock_rules:
            if rule["data_type"] not in seen:
                seen.add(rule["data_type"])
                unique.append(rule)

        return json.dumps(unique, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Prompt Builder
    # -------------------------------------------------------------------------
    def _build_prompt(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Costruisce il prompt per il LLM per un singolo chunk"""
        kb_context = "\n".join(
            f"  - {cat}: {', '.join(items[:6])}"
            for cat, items in self.knowledge_base.items()
        )

        return f"""Analizza questo estratto ({chunk_num}/{total_chunks}) di un documento normativo (GDPR, AI Act o policy aziendale) ed estrai TUTTE le regole, obblighi e divieti sui dati.

CATEGORIE DI RIFERIMENTO:
{kb_context}

TESTO DA ANALIZZARE:
\"\"\"
{chunk}
\"\"\"

ISTRUZIONI:
1. Estrai OGNI tipo di dato soggetto a restrizioni (divieto, obbligo, limite di trattamento)
2. Includi anche obblighi impliciti (es: "il titolare DEVE garantire..." → dato protetto)
3. Per ogni dato estrai:
   - data_type: nome preciso del dato (es: "dati biometrici", "IBAN", "password")
   - category: la categoria dalla lista sopra
   - severity: "critica" (divieto assoluto / violazione grave), "alta" (obbligo/restrizione forte), "media" (raccomandazione), "bassa" (nota informativa)
   - description: breve frase che descrive la regola specifica trovata nel testo

4. SE non ci sono regole in questo estratto, restituisci un array JSON vuoto: []
5. Restituisci SOLO il JSON, senza testo aggiuntivo, senza markdown.

FORMATO RICHIESTO:
[
  {{
    "data_type": "dati biometrici",
    "category": "dati_biometrici",
    "severity": "critica",
    "description": "Vietato il trattamento di dati biometrici per identificazione remota in spazi pubblici (Art. 5 AI Act)"
  }}
]

RISPOSTA (solo JSON):"""

    # -------------------------------------------------------------------------
    # Deduplication
    # -------------------------------------------------------------------------
    def _deduplicate_rules(self, rules: List[Rule]) -> List[Rule]:
        """
        Rimuove regole duplicate basandosi su data_type normalizzato.
        Se ci sono duplicati, tiene quello con la descrizione più lunga (più informativa).
        """
        seen: Dict[str, Rule] = {}
        for rule in rules:
            key = rule.data_type.lower().strip().replace("_", " ").replace("-", " ")
            if key not in seen:
                seen[key] = rule
            else:
                # Tieni la descrizione più lunga
                if len(rule.description) > len(seen[key].description):
                    seen[key] = rule
        return list(seen.values())

    # -------------------------------------------------------------------------
    # Main Pipeline
    # -------------------------------------------------------------------------
    def extract_rules(self, text: str) -> List[Rule]:
        """
        Pipeline RAG completa con chunking:
        1. CHUNK: divide il documento in blocchi sovrapposti
        2. RETRIEVE: per ogni chunk filtra le sezioni rilevanti
        3. GENERATE: il LLM estrae regole da ogni chunk
        4. PARSE: converte le risposte in oggetti Rule
        5. DEDUP: elimina duplicati
        """
        print("✂️  CHUNKING: Divisione del documento in blocchi...")
        chunks = self._split_into_chunks(text)
        print(f"   Creati {len(chunks)} chunk da ~{self.CHUNK_SIZE} caratteri ciascuno")

        all_rules: List[Rule] = []
        total = len(chunks)

        for idx, chunk in enumerate(chunks, start=1):
            print(f"\n🔍 Chunk {idx}/{total} ({len(chunk)} char)...")

            # Retrieval: filtra le sezioni più rilevanti del chunk
            context = self.retrieve_relevant_context(chunk)

            if not context.strip():
                print(f"   ⏭️  Nessun pattern normativo trovato, passo al chunk successivo.")
                continue

            # Generation
            prompt = self._build_prompt(context, idx, total)
            llm_response = self.call_llm(prompt)

            # Parsing
            chunk_rules = self._parse_llm_response(llm_response)
            all_rules.extend(chunk_rules)
            print(f"   ✅ Estratte {len(chunk_rules)} regole (totale finora: {len(all_rules)})")

        print(f"\n🔄 DEDUPLICAZIONE: {len(all_rules)} regole totali...")
        unique_rules = self._deduplicate_rules(all_rules)
        print(f"   ✅ {len(unique_rules)} regole uniche dopo deduplicazione")

        self.rules = unique_rules
        return unique_rules

    # -------------------------------------------------------------------------
    # Parser
    # -------------------------------------------------------------------------
    def _parse_llm_response(self, response: str) -> List[Rule]:
        """Parse della risposta LLM in oggetti Rule"""
        try:
            response = response.strip()

            # Rimuovi blocchi markdown ```json ... ```
            response = re.sub(r"```(?:json)?\s*", "", response)
            response = re.sub(r"```", "", response)
            response = response.strip()

            # Trova il JSON array (anche se ci sono caratteri prima/dopo)
            json_match = re.search(r"\[\s*\{.*?\}\s*\]", response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            elif response == "[]" or response.strip() == "[]":
                return []

            rules_data = json.loads(response)

            if not isinstance(rules_data, list):
                rules_data = [rules_data]

            rules: List[Rule] = []
            valid_severities = {"critica", "alta", "media", "bassa"}

            for rule_dict in rules_data:
                if not isinstance(rule_dict, dict):
                    continue
                data_type = str(rule_dict.get("data_type", "")).strip()
                if not data_type:
                    continue
                severity = str(rule_dict.get("severity", "media")).strip().lower()
                if severity not in valid_severities:
                    severity = "media"
                rule = Rule(
                    data_type=data_type,
                    category=str(rule_dict.get("category", "generale")).strip(),
                    severity=severity,
                    description=str(rule_dict.get("description", "")).strip(),
                )
                rules.append(rule)

            return rules

        except Exception as e:
            print(f"⚠️  Errore nel parsing: {e}")
            if response:
                print(f"   Risposta (prime 200 char): {response[:200]}")
            return []

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------
    def export_to_json(self, output_path: str = "regole_rag.json") -> Dict:
        """Esporta regole in JSON"""
        # Raggruppa per categoria per le statistiche
        categories = sorted(set(r.category for r in self.rules))
        severities = sorted(set(r.severity for r in self.rules))

        output: Dict = {
            "metadata": {
                "total_rules": len(self.rules),
                "categories": categories,
                "severities": severities,
            },
            "regole": [rule.to_dict() for rule in self.rules],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 File JSON salvato: {output_path}")
        return output

    # -------------------------------------------------------------------------
    # PDF text extraction (utility)
    # -------------------------------------------------------------------------
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Estrae testo da PDF (richiede pymupdf: pip install pymupdf)"""
        try:
            import fitz  # type: ignore
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            print("⚠️  PyMuPDF non installato. Installa con: pip install pymupdf")
            return ""
        except Exception as e:
            print(f"❌ Errore nell'estrazione PDF: {e}")
            return ""


# =============================================================================
# Demo / Script diretto
# =============================================================================
def main() -> None:
    print("=" * 80)
    print("🔐 Sistema RAG Migliorato per Estrazione Regole da PDF")
    print("=" * 80)

    api_config = {
        "url": "http://localhost:11434/api/chat",
        "model": "llama3.1:latest",
    }

    extractor = SimpleRAGExtractor(api_config=api_config)

    policy_text = """
    REGOLAMENTO AZIENDALE SULLA PROTEZIONE DEI DATI (conforme a GDPR e AI Act)

    Articolo 1 - Dati Personali
    È assolutamente vietato pubblicare o condividere i seguenti dati:
    - Nome e cognome completi, indirizzo, telefono, email, codice fiscale,
      numero di carta d'identità o passaporto, data e luogo di nascita.

    Articolo 2 - Dati Finanziari
    È proibito divulgare IBAN, numeri di carta di credito, stipendi, fatturato,
    bilanci e budget di progetto.

    Articolo 3 - Credenziali
    Password, PIN, token, API key, certificati digitali e chiavi private
    sono strettamente riservati e non devono mai essere condivisi.

    Articolo 4 - Dati Tecnici
    Non condividere indirizzi IP interni, configurazioni di rete, vulnerabilità,
    architetture IT, nomi di database e server.

    Articolo 5 - Segreti Aziendali
    Brevetti, segreti industriali, strategie, roadmap e contratti sono riservati.

    Articolo 6 - Dati Sanitari e Biometrici (AI Act Art. 5)
    È vietato il trattamento di dati biometrici per l'identificazione remota
    in tempo reale in spazi accessibili al pubblico. Le cartelle cliniche,
    diagnosi, terapie e dati genetici devono essere protetti con misure rafforzate.

    Articolo 7 - Sistemi IA ad Alto Rischio
    I dataset di addestramento, i parametri dei modelli IA e i sistemi di
    punteggio sociale sono vietati. I sistemi di sorveglianza biometrica devono
    rispettare i requisiti del Titolo III AI Act. Non è consentito utilizzare
    sistemi IA che sfruttino vulnerabilità cognitive o manipolino comportamenti.
    """

    rules = extractor.extract_rules(policy_text)

    print("\n" + "=" * 80)
    print("📊 RISULTATI")
    print("=" * 80)

    by_category: Dict[str, List[Rule]] = {}
    for rule in rules:
        by_category.setdefault(rule.category, []).append(rule)

    for category, cat_rules in sorted(by_category.items()):
        print(f"\n📁 {category.upper().replace('_', ' ')} ({len(cat_rules)})")
        print("-" * 60)
        for rule in cat_rules:
            icon = {"critica": "🔴", "alta": "🟠", "media": "🟡", "bassa": "🟢"}.get(rule.severity, "⚪")
            print(f"  {icon} {rule.data_type} [{rule.severity}]")
            if rule.description:
                print(f"     → {rule.description}")

    output = extractor.export_to_json()
    print(f"\n📈 Statistiche: {output['metadata']['total_rules']} regole | "
          f"{len(output['metadata']['categories'])} categorie")
    print("✅ Elaborazione completata!")


if __name__ == "__main__":
    main()
