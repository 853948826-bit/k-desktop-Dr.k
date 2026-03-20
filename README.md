User Instruction
│
▼
┌─────────────────┐
│ κ-Router │ ← Computes κ, selects execution path
│ (Phase Detector) │
└────────┬─────────┘
│
┌─────┼─────┐
▼ ▼ ▼
┌─────┐ ┌─────┐ ┌─────┐
│ Gas │ │ Liq │ │ Cry │
│ LLM │ │ Tpl │ │Rule │
└─────┘ └─────┘ └─────┘
▼ ▼ ▼
Desktop Action Executed



## 🚀 Quick Start

### Prerequisites

```bash
pip install matplotlib numpy
# Optional: for LLM integration
pip install httpx
# Optional: for desktop automation
pip install pyautogui
Run Simulation (No API Key Needed)

python black_box.py
Run with Local LLM (Ollama)

# 1. Install Ollama: https://ollama.ai
# 2. Pull a model
ollama pull gemma3:4b

# 3. Run experiment
python black_box.py --live --backend=ollama
Run with DeepSeek API

export DEEPSEEK_API_KEY=sk-your-key-here
python black_box.py --live --backend=deepseek
Run Full Experiment

python run_full_experiment.py
Generate Paper Figures

python generate_llm_figures.py
python fix_figure8.py
📊 Key Results
From our live experiment with Gemma3:4B (local LLM):

Metric	Value
Total instructions	25
Success rate	92% (23/25)
Phase transitions observed	5
LLM calls required	8/25 (32%)
LLM cost reduction	68%
Theory-experiment agreement	R² = 1.0000
Phase Transitions Observed

⚡ gas → liquid    at κ = 0.26 → 0.42 (n=2)
⚡ liquid → crystal at κ = 0.79 → 0.83 (n=7)
⚡ gas → liquid    at κ = 0.26 → 0.42 (n=2)
⚡ liquid → crystal at κ = 0.79 → 0.83 (n=7)
⚡ gas → liquid    at κ = 0.26 → 0.42 (n=2)
📁 Project Structure

kappa-desktop/
├── README.md                    # This file
├── LICENSE                      # Apache 2.0
├── .gitignore                   # Python gitignore
│
├── black_box.py                 # LLM backend + κ-Router
├── run_full_experiment.py       # Full experiment script
├── generate_llm_figures.py      # Figure generation
├── fix_figure8.py               # Cost analysis figure
├── requirements.txt             # Python dependencies
│
├── data/
│   └── full_experiment_ollama.json  # Experiment data
│
└── paper/
    ├── kappa_desktop.tex        # LaTeX source
    ├── kappa_desktop.pdf        # Compiled paper
    └── figure*.png              # Paper figures
📄 Paper
"κ-Desktop: An Information Phase Transition Framework for
Adaptive Desktop Automation"

SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5217017
DOI: 10.2139/ssrn.5217017
Citation

@article{kdesktop2025,
  title     = {$\kappa$-Desktop: An Information Phase Transition 
               Framework for Adaptive Desktop Automation},
  author    = {Dr. K},
  journal   = {SSRN Electronic Journal},
  year      = {2025},
  doi       = {10.2139/ssrn.5217017},
  url       = {https://papers.ssrn.com/abstract=5217017}
}
🔬 Theoretical Foundation
The κ framework is built on three core equations:

1. Growth Law
κ(n)=κ 
max
​
 (1−e 
−λn
 )+κ 
min
​
 

where n = number of successful executions, λ = learning rate.

2. Phase Boundaries
Phase= 
⎩
⎨
⎧
​
  
Gas (Black Box)
Liquid (Grey Box)
Crystal (White Box)
​
  
κ<κ 
c1
​
 =0.3
κ 
c1
​
 ≤κ<κ 
c2
​
 =0.8
κ≥κ 
c2
​
 =0.8
​
 

3. Entropy
H(κ)=−κlog 
2
​
 κ−(1−κ)log 
2
​
 (1−κ)

🗺️ Roadmap
 Core κ growth model
 Three-box architecture
 LLM integration (Ollama, DeepSeek, OpenAI)
 Live experiment with phase transitions
 SSRN paper published
 Multi-user κ sharing
 Visual workflow editor
 Plugin system for custom actions
 Cloud deployment (OPC)
 Mobile support
📜 License
This project is licensed under the Apache License 2.0 — see the LICENSE file for details.

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/amazing)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing)
Open a Pull Request
Built with 🔬 by Dr. K | OPC (Opening, 2025)
