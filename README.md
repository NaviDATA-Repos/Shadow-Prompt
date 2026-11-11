Shadow Prompt - supplementary material

dataset/
  shadow_prompt_dataset_810.csv
    The 810 test inputs (mostly Italian), generated with Claude Sonnet 4.6 and used as generated.
    label: "sensitive" if the reference output contains a mask (***), otherwise "non-sensitive"
           (670 sensitive, 140 non-sensitive).
    llama3_8b_output / deepseek_r1_8b_output: model outputs recorded in the tests, with response times in ms.
    The input text is taken from the llama3:8b test file; in the deepseek-r1:8b test file input 385
    has one extra trailing character ("A"), the other 809 inputs are identical.

annotation/
  annotation_sample_supplementary_EN.xlsx
    Stratified sample of 130 model outputs (65 per model) labelled by three anonymized raters
    (fully masked / partially masked / uncertain), used to estimate partial masking.

presidio_baseline/
  presidio_baseline.py   reproducible Microsoft Presidio baseline (usage in the file header)
  presidio_results.csv   per-input results; columns A-D are the four configurations
                         (A default, B without ORGANIZATION/NRP, C also without DATE_TIME/URL, D pattern recognizers only)

extension/
  original/      browser extension as evaluated (fail-open)
  fail_closed/   variant that blocks submission until the masking check has succeeded
  Both folders include validated_policies.json, the 27 rules written manually by the authors.

failure_tests/
  ollama_mock.py  stub of the Ollama endpoint (modes: ok, timeout, invalid, http500)
  site.py         mock chat page that records what leaves the browser
  run_tests.py    Playwright runner (python run_tests.py orig fc)
  results.csv     results of both extensions
  The tests use a stub server and a mock page, not real Ollama or real chatbot interfaces.

policy_extraction/
  Offline RAG policy-extraction pipeline (simple_rag.py and helpers). It was not used to build the
  knowledge base of the evaluation. API keys and local paths have been removed.
