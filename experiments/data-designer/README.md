# Data Designer (local)

Phase 0 lockdown for the studio's synthetic-data builder. NeMo Data Designer
0.9.4, local Ollama only. Later phases are not started.

## Lock

- Python pin: `python-pin.txt` (3.14.5). The venv is `.venv` and is not committed.
- Package pin: `requirements.txt` (`data-designer==0.9.4`). The full environment
  is `requirements.lock`. Torch is not installed.
- The only provider is `ollama-local` at `http://127.0.0.1:11434/v1`.
  `home/model_providers.yaml` is written before the library starts, so the
  default remote providers are never written.
- `studio_lock.arm()` sets `NEMO_TELEMETRY_ENABLED=false` before import.
  `import_data_designer()` refuses any other value, including an unset variable.
- Model names containing `cloud` are refused.
- Column token stats use a local byte-length counter. Data Designer's preview
  footnote still says those counts come from tiktoken's cl100k_base. They do
  not. The job refuses that tokenizer so the encoding cannot be downloaded.

## Checks

From this directory:

```
.venv\Scripts\python.exe -m unittest tests.test_lockdown -v
```

Five tests, no GPU: telemetry unset fails, telemetry is off after arm, the
provider list is only `ollama-local`, a cloud model name is refused, and a
one-row stub job stays on localhost.

## Smoke

`one_row.py` loads `mistral-small:24b` only when `STUDIO_GPU_GRANT` is the
string `granted` and no other model is loaded. The digest must be
`8039dd90c113`. That run has not happened yet. Outputs stay in this experiment.
Nothing is uploaded.
