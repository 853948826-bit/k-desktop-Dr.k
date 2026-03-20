# κ-Desktop: Information Phase Transition Theory for Desktop Automation

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![SSRN Paper](https://img.shields.io/badge/SSRN-5217017-green.svg)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5217017)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-yellow.svg)](https://python.org)

> **A novel theoretical framework that models desktop automation as an information phase transition system, inspired by thermodynamic phase transitions (Gas → Liquid → Crystal).**

<p align="center">
  <img src="paper/figure7_llm_experiment.png" width="90%" alt="κ-Desktop Experiment Results">
</p>

---

## 📖 Overview

κ-Desktop introduces the **Information Precision Index** κ ∈ [0, 1] to quantify how well a system "understands" a user's desktop instruction. As the system gains experience with repeated tasks, κ grows following an exponential saturation law:

$$\kappa(n) = \kappa_{\max}(1 - e^{-\lambda n}) + \kappa_{\min}$$

This growth drives **phase transitions** between three execution backends:

| Phase | κ Range | Backend | Description |
|:------|:--------|:--------|:------------|
| 🔴 **Gas** | κ < 0.3 | Black Box (LLM) | Unknown tasks → call LLM for interpretation |
| 🟡 **Liquid** | 0.3 ≤ κ < 0.8 | Grey Box (Template) | Familiar tasks → use learned templates |
| 🔵 **Crystal** | κ ≥ 0.8 | White Box (Rule) | Mastered tasks → execute deterministic rules |

### The Three-Box Architecture
