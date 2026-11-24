# ai-security-lab

Hands-on AI security experiments — from prompt injection (inference-time) to federated gradient leakage (training-time).

Built while learning AI security, as part of a transition from clinical medicine into ML × security.

## Experiments

| Lab | Topic | File |
|---|---|---|
| 1 | Prompt injection basics — rule-ignore / role-play / base64 bypass | `lab01_injection.py` |
| 2 | System-prompt leakage + multi-turn injection | `lab02_injection.py` |
| 3 | Federated gradient leakage — exact recovery from gradients + DP trade-off | `lab03_federated_gradient_leak.py` |

## Requirements

- Python 3 (lab03 needs `numpy`; lab01/02 use only the standard library)
- A local LLM via [Ollama](https://ollama.com) with a model named `qwen1.5-7b` (or edit `MODEL` in the scripts)

## Run

```bash
ollama pull qwen1.5-7b          # for lab01/02
python3 lab01_injection.py
python3 lab02_injection.py
python3 lab03_federated_gradient_leak.py   # numpy only, no Ollama needed
```

## What each lab shows

- **lab01** — a model told "never reveal secrets" still leaks them via "ignore all rules", role-play, and base64 encoding: the classic prompt-injection surface.
- **lab02** — the system prompt itself can be extracted, and multi-turn conversations lower the barrier further.
- **lab03** — in federated learning, uploading *gradients* (not raw data) is not safe: a single sample's gradients let a malicious server *exactly* recover the private input, and differential-privacy noise trades utility against privacy.

## Next steps

Reproduce multi-sample attacks ([GGL](https://github.com/zhuohangli/GGL), [E2EGI](https://github.com/zhaohuali/E2EGI)) and defenses ([Soteria](https://github.com/jeremy313/Soteria), [DPFL](https://github.com/zlh-thu/DPFL)) toward an open federated-security benchmark.

## Disclaimer

Educational and defensive only. Run only against models and systems you own.
