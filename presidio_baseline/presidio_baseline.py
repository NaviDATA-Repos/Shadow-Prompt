"""Baseline Presidio sugli 810 casi di Shadow Prompt.
Uso:  pip install presidio-analyzer spacy pandas openpyxl
      python -m spacy download it_core_news_lg && python -m spacy download en_core_web_lg
      python presidio_baseline.py shadowguard_test_llama.xlsx
Ground truth: positivo se 'Expected Output (masked)' contiene ***.
Criterio 'mascherato': Presidio rileva almeno un'entita' con score >= 0.4 (stesso criterio permissivo usato per gli LLM:
una rilevazione qualsiasi conta come TP, senza verificare che copra l'intero dato sensibile).
Si analizza ogni frase in italiano e in inglese e si fa l'unione delle rilevazioni."""
import sys, warnings, logging, pandas as pd
warnings.filterwarnings('ignore'); logging.disable(logging.CRITICAL)
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

def make(lang, model):
    nlp = NlpEngineProvider(nlp_configuration={'nlp_engine_name': 'spacy',
          'models': [{'lang_code': lang, 'model_name': model}]}).create_engine()
    reg = RecognizerRegistry(supported_languages=[lang])
    reg.load_predefined_recognizers(nlp_engine=nlp, languages=[lang])
    return AnalyzerEngine(nlp_engine=nlp, registry=reg, supported_languages=[lang])

A = {'it': make('it', 'it_core_news_lg'), 'en': make('en', 'en_core_web_lg')}
VARIANTI = {   # entita' escluse per variante
 'A_default': (),
 'B_senza_ORG_NRP': ('ORGANIZATION', 'NRP'),
 'C_senza_ORG_NRP_DATE_URL': ('ORGANIZATION', 'NRP', 'DATE_TIME', 'URL'),
 'D_solo_pattern': ('PERSON', 'LOCATION', 'ORGANIZATION', 'NRP', 'DATE_TIME', 'URL'),
}
TH = 0.4
df = pd.read_excel(sys.argv[1], sheet_name='Test Cases')
df['GT'] = df['Expected Output (masked)'].fillna('').astype(str).str.contains('***', regex=False)
raw = []
for ph in df['Test Phrase'].astype(str):
    sp = []
    for lang in ('it', 'en'):
        sp += [(x.entity_type, x.score) for x in A[lang].analyze(text=ph, language=lang, score_threshold=0.0)]
    raw.append(sp)
for nome, drop in VARIANTI.items():
    df[nome] = [any(s >= TH and e not in drop for e, s in sp) for sp in raw]
    m = df[nome]; g = df['GT']
    TP, FN, FP, TN = int((g & m).sum()), int((g & ~m).sum()), int((~g & m).sum()), int((~g & ~m).sum())
    R = TP/(TP+FN); P = TP/(TP+FP); print(f"{nome}: TP={TP} FN={FN} FP={FP} TN={TN} Recall={R:.3f} Prec={P:.3f} F1={2*P*R/(P+R):.3f} FPR={FP/(FP+TN):.3f}")
df[['Data Type', 'Category', 'Difficulty', 'Test Phrase', 'GT'] + list(VARIANTI)].to_csv('presidio_results.csv', index=False)
