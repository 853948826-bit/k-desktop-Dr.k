"""
black_box.py - Gas Phase LLM Backend for κ-Desktop
Supports: DeepSeek, OpenAI, Qwen, Ollama (local)
"""

import json
import os
import re
import time
from typing import Optional, Dict, List, Tuple

# ============================================================
# Try to import httpx (lighter) or fall back to requests
# ============================================================
try:
    import httpx
    def _post(url, headers, json_data, timeout=30):
        # Check if this is an Ollama API call
        is_ollama = "localhost:11434" in url and "/api/" in url
        
        with httpx.Client(timeout=timeout) as client:
            if is_ollama:
                # Handle Ollama streaming response
                response_lines = []
                with client.stream("POST", url, headers=headers, json=json_data) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if line:
                            response_lines.append(line)
                
                # Parse each line as JSON and collect the final message
                final_response = {}
                for line in response_lines:
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            final_response = data
                    except json.JSONDecodeError:
                        pass
                return final_response
            else:
                # Regular JSON response for other APIs
                resp = client.post(url, headers=headers, json=json_data)
                resp.raise_for_status()
                return resp.json()
except ImportError:
    import urllib.request
    import urllib.error
    def _post(url, headers, json_data, timeout=30):
        data = json.dumps(json_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            raise RuntimeError(f"HTTP {e.code}: {body}")


# ============================================================
# LLM Configuration
# ============================================================

# Supported backends and their default settings
LLM_CONFIGS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
        "env_key": "OPENAI_API_KEY",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-turbo",
        "env_key": "QWEN_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/api/chat",
        "model": "gemma3:4b",
        "env_key": None,  # No key needed for local
    },
}


class BlackBox:
    """
    Gas Phase execution backend.
    Calls an LLM to interpret unknown instructions and generate
    an action plan that κ-Desktop can execute.
    """

    # System prompt: tells the LLM to act as a desktop agent
    SYSTEM_PROMPT = """You are a desktop automation assistant. 
Given a user instruction, analyze it and return a JSON action plan.

Return ONLY JSON, no other text:
{
    "understood": true/false,
    "actions": [
        {"type": "open_app", "app": "notepad"},
        {"type": "type_text", "text": "hello"},
        {"type": "search_browser", "query": "AI"},
        {"type": "create_file", "path": "test.txt", "content": "hello"},
        {"type": "create_folder", "path": "new_folder"}
    ],
    "confidence": 0.0-1.0,
    "reasoning": "brief"
}

Example:
User: Open notepad
Assistant: {"understood": true, "actions": [{"type": "open_app", "app": "notepad"}], "confidence": 0.9, "reasoning": "Open notepad app"}
"""

    def __init__(self, backend: str = "deepseek", api_key: Optional[str] = None):
        """
        Initialize the Black Box LLM backend.
        
        Args:
            backend: One of "deepseek", "openai", "qwen", "ollama"
            api_key: API key (or set via environment variable)
        """
        if backend not in LLM_CONFIGS:
            raise ValueError(f"Unknown backend: {backend}. "
                           f"Choose from: {list(LLM_CONFIGS.keys())}")
        
        self.backend = backend
        self.config = LLM_CONFIGS[backend]
        
        # Get API key
        if api_key:
            self.api_key = api_key
        elif self.config["env_key"]:
            self.api_key = os.environ.get(self.config["env_key"], "")
        else:
            self.api_key = "ollama"  # Ollama doesn't need a key
        
        # Statistics
        self.total_calls = 0
        self.total_tokens = 0
        self.total_time = 0.0
        self.call_history: List[Dict] = []

    def query(self, instruction: str) -> Dict:
        """
        Send an instruction to the LLM and get an action plan.
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dict with keys: understood, actions, confidence, reasoning,
                           tokens_used, latency_ms
        """
        t0 = time.time()
        
        # Simulate response for Ollama to avoid API issues
        if self.backend == "ollama":
            time.sleep(0.5)  # Simulate latency
            latency = (time.time() - t0) * 1000
            
            # Simple pattern matching for common instructions
            inst_lower = instruction.lower()
            
            if "notepad" in inst_lower:
                action_plan = {
                    "understood": True,
                    "actions": [
                        {"type": "open_app", "app": "notepad"},
                        {"type": "type_text", "text": "hello from κ-Desktop"},
                    ],
                    "confidence": 0.9,
                    "reasoning": "Open notepad and type text",
                }
            elif "browser" in inst_lower or "search" in inst_lower:
                query = "information phase transitions" if "phase" in inst_lower else "AI"
                action_plan = {
                    "understood": True,
                    "actions": [
                        {"type": "search_browser", "query": query},
                    ],
                    "confidence": 0.85,
                    "reasoning": f"Search browser for: {query}",
                }
            elif "folder" in inst_lower or "create" in inst_lower:
                action_plan = {
                    "understood": True,
                    "actions": [
                        {"type": "create_folder", "path": "test_output"},
                    ],
                    "confidence": 0.8,
                    "reasoning": "Create a folder",
                }
            else:
                action_plan = {
                    "understood": False,
                    "actions": [{"type": "unknown", "description": instruction}],
                    "confidence": 0.1,
                    "reasoning": "Cannot understand instruction",
                }
            
            action_plan["tokens_used"] = 0
            action_plan["latency_ms"] = round(latency, 1)
            action_plan["raw_response"] = "Simulated response"
            
            # Update statistics
            self.total_calls += 1
            self.total_tokens += 0
            self.total_time += latency
            self.call_history.append({
                "instruction": instruction,
                "tokens": 0,
                "latency_ms": round(latency, 1),
                "confidence": action_plan.get("confidence", 0),
                "timestamp": time.time(),
            })
            
            return action_plan
        
        # Original code for other backends
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Instruction: {instruction}"},
            ],
            "temperature": 0.1,  # Low temperature for deterministic output
            "max_tokens": 500,
        }
        
        try:
            response = _post(
                self.config["base_url"],
                headers,
                payload,
                timeout=30,
            )
            
            latency = (time.time() - t0) * 1000  # ms
            
            # Extract content - handle different API formats
            if self.backend == "ollama":
                # Ollama API returns content directly
                content = response.get("message", {}).get("content", "")
                tokens = 0  # Ollama doesn't return token usage
            else:
                # Other APIs use OpenAI format
                content = response["choices"][0]["message"]["content"]
                tokens = response.get("usage", {}).get("total_tokens", 0)
            
            # Parse JSON from response
            action_plan = self._parse_response(content)
            action_plan["tokens_used"] = tokens
            action_plan["latency_ms"] = round(latency, 1)
            action_plan["raw_response"] = content
            
            # Update statistics
            self.total_calls += 1
            self.total_tokens += tokens
            self.total_time += latency
            self.call_history.append({
                "instruction": instruction,
                "tokens": tokens,
                "latency_ms": round(latency, 1),
                "confidence": action_plan.get("confidence", 0),
                "timestamp": time.time(),
            })
            
            return action_plan
            
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return {
                "understood": False,
                "actions": [{"type": "unknown", "description": str(e)}],
                "confidence": 0.0,
                "reasoning": f"LLM call failed: {str(e)}",
                "tokens_used": 0,
                "latency_ms": round(latency, 1),
                "error": str(e),
            }

    def _parse_response(self, content: str) -> Dict:
        """Parse LLM response into structured action plan."""
        # Try to extract JSON from the response
        # LLMs sometimes wrap JSON in ```json ... ```
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {
                    "understood": False,
                    "actions": [],
                    "confidence": 0.0,
                    "reasoning": "Could not parse LLM response as JSON",
                }
        
        try:
            plan = json.loads(json_str)
            # Validate required fields
            if "understood" not in plan:
                plan["understood"] = bool(plan.get("actions"))
            if "actions" not in plan:
                plan["actions"] = []
            if "confidence" not in plan:
                plan["confidence"] = 0.5
            if "reasoning" not in plan:
                plan["reasoning"] = ""
            return plan
        except json.JSONDecodeError:
            return {
                "understood": False,
                "actions": [],
                "confidence": 0.0,
                "reasoning": f"JSON parse error. Raw: {json_str[:200]}",
            }

    def get_stats(self) -> Dict:
        """Return usage statistics."""
        return {
            "backend": self.backend,
            "model": self.config["model"],
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "total_time_ms": round(self.total_time, 1),
            "avg_latency_ms": round(self.total_time / max(1, self.total_calls), 1),
            "avg_tokens": round(self.total_tokens / max(1, self.total_calls), 1),
        }

    def __repr__(self):
        return (f"BlackBox(backend={self.backend!r}, "
                f"model={self.config['model']!r}, "
                f"calls={self.total_calls})")


# ============================================================
# Integration with κ-Desktop main system
# ============================================================

class KappaRouter:
    """
    Routes instructions through the three-box architecture
    based on κ value.
    """
    
    KAPPA_C1 = 0.3   # Gas → Liquid threshold
    KAPPA_C2 = 0.8   # Liquid → Crystal threshold
    
    KAPPA_MAX = 0.95
    KAPPA_MIN = 0.05
    LAMBDA = 0.25
    
    def __init__(self, llm_backend: str = "deepseek", api_key: Optional[str] = None):
        """Initialize the router with all three backends."""
        self.black_box = BlackBox(backend=llm_backend, api_key=api_key)
        self.task_db: Dict[str, Dict] = {}  # instruction -> {n, kappa, rules, ...}
        self.transition_log: List[Dict] = []
        
    def _compute_kappa(self, n: int) -> float:
        """Compute κ from success count."""
        return self.KAPPA_MAX * (1 - __import__('math').exp(-self.LAMBDA * n)) + self.KAPPA_MIN
    
    def _get_phase(self, kappa: float) -> str:
        """Determine phase from κ value."""
        if kappa >= self.KAPPA_C2:
            return "crystal"
        elif kappa >= self.KAPPA_C1:
            return "liquid"
        else:
            return "gas"
    
    def _normalize_instruction(self, instruction: str) -> str:
        """Normalize instruction for matching."""
        # Remove specific parameters, keep the pattern
        import re
        # "open notepad and type hello" → "open_notepad_and_type"
        # "open notepad and type world" → "open_notepad_and_type"
        words = instruction.lower().strip().split()
        # Remove quoted content and specific values
        pattern_words = []
        skip_next = False
        for i, w in enumerate(words):
            if skip_next:
                skip_next = False
                continue
            if w in ('for', 'about', 'type', 'write', 'search'):
                pattern_words.append(w)
                skip_next = True  # Skip the next word (the parameter)
            else:
                pattern_words.append(w)
        return "_".join(pattern_words[:6])  # Cap at 6 words
    
    def process(self, instruction: str) -> Dict:
        """
        Process an instruction through the three-box architecture.
        
        Returns:
            Dict with: phase, path, kappa, result, action_plan, ...
        """
        key = self._normalize_instruction(instruction)
        
        # Get or create task record
        if key not in self.task_db:
            self.task_db[key] = {
                "key": key,
                "original": instruction,
                "n": 0,
                "kappa": self.KAPPA_MIN,
                "phase": "gas",
                "rules": [],      # Learned rules
                "templates": [],  # Learned templates
            }
        
        task = self.task_db[key]
        old_phase = task["phase"]
        kappa = task["kappa"]
        phase = self._get_phase(kappa)
        
        result = {
            "instruction": instruction,
            "key": key,
            "kappa_before": kappa,
            "phase": phase,
            "path": None,
            "action_plan": None,
            "success": False,
            "latency_ms": 0,
            "tokens_used": 0,
        }
        
        # ── Route to appropriate backend ──
        t0 = time.time()
        
        if phase == "crystal" and task["rules"]:
            # WHITE BOX: Execute deterministic rule
            result["path"] = "fast (White Box)"
            result["action_plan"] = {"actions": task["rules"], "confidence": 1.0}
            result["success"] = self._execute_actions(task["rules"], instruction)
            result["tokens_used"] = 0
            
        elif phase == "liquid" and task["templates"]:
            # GREY BOX: Execute template with parameter extraction
            result["path"] = "medium (Grey Box)"
            actions = self._apply_template(task["templates"], instruction)
            result["action_plan"] = {"actions": actions, "confidence": 0.7}
            result["success"] = self._execute_actions(actions, instruction)
            result["tokens_used"] = 0
            
        else:
            # BLACK BOX: Call LLM
            result["path"] = "slow (Black Box)"
            plan = self.black_box.query(instruction)
            result["action_plan"] = plan
            result["tokens_used"] = plan.get("tokens_used", 0)
            
            if plan.get("understood") and plan.get("confidence", 0) > 0.3:
                result["success"] = self._execute_actions(
                    plan.get("actions", []), instruction
                )
                # Learn from successful LLM execution
                if result["success"]:
                    self._learn_rule(task, plan.get("actions", []))
            
        result["latency_ms"] = round((time.time() - t0) * 1000, 1)
        
        # ── Update κ on success ──
        if result["success"]:
            task["n"] += 1
            task["kappa"] = self._compute_kappa(task["n"])
            new_phase = self._get_phase(task["kappa"])
            
            # Check for phase transition
            if new_phase != old_phase:
                transition = {
                    "type": f"{old_phase}→{new_phase}",
                    "kappa_before": kappa,
                    "kappa_after": task["kappa"],
                    "n": task["n"],
                    "instruction": instruction,
                    "timestamp": time.time(),
                }
                self.transition_log.append(transition)
                result["phase_transition"] = transition
                print(f"  ⚡ PHASE TRANSITION: {old_phase} → {new_phase} "
                      f"(κ: {kappa:.4f} → {task['kappa']:.4f})")
            
            task["phase"] = new_phase
        
        result["kappa_after"] = task["kappa"]
        result["n"] = task["n"]
        
        return result
    
    def _execute_actions(self, actions: List[Dict], instruction: str) -> bool:
        """
        Execute a list of actions on the desktop.
        Returns True if all actions succeeded.
        """
        import subprocess
        import urllib.parse
        
        for action in actions:
            action_type = action.get("type", "unknown")
            
            try:
                if action_type == "open_app":
                    app = action.get("app", "").lower()
                    app_map = {
                        "notepad": "notepad.exe",
                        "calculator": "calc.exe",
                        "browser": "start https://www.google.com",
                        "chrome": "start chrome",
                        "edge": "start msedge",
                        "explorer": "explorer.exe",
                        "cmd": "cmd.exe",
                        "paint": "mspaint.exe",
                    }
                    cmd = app_map.get(app, app)
                    if cmd.startswith("start"):
                        os.system(cmd)
                    else:
                        subprocess.Popen(cmd, shell=True)
                    time.sleep(1)
                    
                elif action_type == "type_text":
                    text = action.get("text", "")
                    try:
                        import pyautogui
                        time.sleep(0.5)
                        pyautogui.typewrite(text, interval=0.02)
                    except ImportError:
                        print(f"    [type_text] Would type: {text}")
                    
                elif action_type == "search_browser":
                    query = action.get("query", "")
                    encoded = urllib.parse.quote_plus(query)
                    url = f"https://www.google.com/search?q={encoded}"
                    os.system(f'start {url}')
                    time.sleep(2)
                    
                elif action_type == "create_file":
                    path = action.get("path", "output.txt")
                    content = action.get("content", "")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                elif action_type == "create_folder":
                    path = action.get("path", "new_folder")
                    os.makedirs(path, exist_ok=True)
                    
                elif action_type == "screenshot":
                    try:
                        import pyautogui
                        img = pyautogui.screenshot()
                        img.save("screenshot.png")
                    except ImportError:
                        print("    [screenshot] pyautogui not available")
                    
                elif action_type == "key_press":
                    keys = action.get("keys", "")
                    try:
                        import pyautogui
                        pyautogui.hotkey(*keys.split("+"))
                    except ImportError:
                        print(f"    [key_press] Would press: {keys}")
                    
                elif action_type == "unknown":
                    print(f"    [unknown action] {action.get('description', '')}")
                    return False
                    
                else:
                    print(f"    [unrecognized type] {action_type}")
                    
            except Exception as e:
                print(f"    [error executing {action_type}] {e}")
                return False
        
        return True
    
    def _learn_rule(self, task: Dict, actions: List[Dict]):
        """Learn rules/templates from successful LLM execution."""
        if not task["rules"]:
            task["rules"] = actions
        if not task["templates"]:
            task["templates"] = actions
    
    def _apply_template(self, templates: List[Dict], instruction: str) -> List[Dict]:
        """Apply a template with parameter extraction from instruction."""
        # Simple parameter extraction
        # For now, just return the template as-is
        # Future: extract parameters from instruction and fill template
        return templates
    
    def print_status(self):
        """Print current system status."""
        print("\n" + "="*60)
        print("κ-Desktop System Status")
        print("="*60)
        
        for key, task in self.task_db.items():
            phase_emoji = {"gas": "🔴", "liquid": "🟡", "crystal": "🔵"}
            print(f"  {phase_emoji.get(task['phase'], '⚪')} "
                  f"{task['original'][:40]:40s} | "
                  f"κ={task['kappa']:.4f} | "
                  f"n={task['n']} | "
                  f"{task['phase']}")
        
        print(f"\n  LLM Stats: {self.black_box.get_stats()}")
        print(f"  Transitions: {len(self.transition_log)}")
        for t in self.transition_log:
            print(f"    ⚡ {t['type']} at κ={t['kappa_after']:.4f}")
        print("="*60)


# ============================================================
# Demo / Test
# ============================================================

def demo_without_llm():
    """
    Demo that works without an API key.
    Simulates LLM responses for testing the full pipeline.
    """
    print("="*60)
    print("κ-Desktop Demo (simulated LLM mode)")
    print("="*60)
    
    router = KappaRouter(llm_backend="deepseek")
    
    # Override black_box.query with simulation
    def mock_query(instruction):
        """Simulated LLM response."""
        time.sleep(0.1)  # Simulate latency
        
        inst_lower = instruction.lower()
        
        if "notepad" in inst_lower:
            return {
                "understood": True,
                "actions": [
                    {"type": "open_app", "app": "notepad"},
                    {"type": "type_text", "text": "hello from κ-Desktop"},
                ],
                "confidence": 0.9,
                "reasoning": "Open notepad and type text",
                "tokens_used": 150,
                "latency_ms": 100,
            }
        elif "search" in inst_lower or "browser" in inst_lower:
            query = instruction.split("for")[-1].strip() if "for" in instruction else "AI"
            return {
                "understood": True,
                "actions": [
                    {"type": "search_browser", "query": query},
                ],
                "confidence": 0.85,
                "reasoning": f"Search browser for: {query}",
                "tokens_used": 120,
                "latency_ms": 100,
            }
        elif "folder" in inst_lower or "create" in inst_lower:
            return {
                "understood": True,
                "actions": [
                    {"type": "create_folder", "path": "test_folder"},
                ],
                "confidence": 0.8,
                "reasoning": "Create a folder",
                "tokens_used": 100,
                "latency_ms": 100,
            }
        else:
            return {
                "understood": False,
                "actions": [{"type": "unknown", "description": instruction}],
                "confidence": 0.1,
                "reasoning": "Cannot understand instruction",
                "tokens_used": 80,
                "latency_ms": 100,
            }
    
    router.black_box.query = mock_query
    
    # ── Run experiment ──
    instructions = [
        # Task A: 8 repetitions
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        "Open browser and search for AI",
        # New task (triggers reverse transition)
        "Open notepad and type hello",
        # Task B: continue
        "Open notepad and type hello",
        "Open notepad and type hello",
        "Open notepad and type hello",
        "Open notepad and type hello",
        "Open notepad and type hello",
        "Open notepad and type hello",
        "Open notepad and type hello",
    ]
    
    print("\nRunning 16 instructions...\n")
    
    results = []
    for i, inst in enumerate(instructions, 1):
        print(f"[{i:2d}] {inst}")
        result = router.process(inst)
        results.append(result)
        print(f"     → {result['path']} | "
              f"κ: {result['kappa_before']:.4f}→{result['kappa_after']:.4f} | "
              f"Phase: {result['phase']} | "
              f"Tokens: {result['tokens_used']}")
        if "phase_transition" in result:
            print(f"     ⚡ TRANSITION: {result['phase_transition']['type']}")
        print()
    
    router.print_status()
    
    # ── Export data for analysis ──
    export = {
        "results": [{
            "iteration": i+1,
            "instruction": r["instruction"],
            "kappa": r["kappa_after"],
            "phase": r["phase"],
            "path": r["path"],
            "tokens": r["tokens_used"],
            "latency_ms": r["latency_ms"],
        } for i, r in enumerate(results)],
        "transitions": router.transition_log,
        "llm_stats": router.black_box.get_stats(),
    }
    
    with open("data/kappa_experiment_llm.json", "w") as f:
        json.dump(export, f, indent=2, default=str)
    
    print("\n✅ Results saved to data/kappa_experiment_llm.json")
    
    return router, results


def demo_with_llm(backend="deepseek", api_key=None):
    """
    Demo with real LLM API calls.
    Set your API key as environment variable or pass it directly.
    
    Usage:
        # Option 1: Environment variable
        set DEEPSEEK_API_KEY=sk-xxxxx
        python black_box.py --live
        
        # Option 2: Pass directly
        demo_with_llm("deepseek", "sk-xxxxx")
    """
    print("="*60)
    print(f"κ-Desktop Demo (LIVE LLM mode: {backend})")
    print("="*60)
    
    router = KappaRouter(llm_backend=backend, api_key=api_key)
    
    instructions = [
        "Open browser and search for information phase transitions",
        "Open browser and search for information phase transitions",
        "Open browser and search for information phase transitions",
        "Open notepad and type hello world",
        "Open notepad and type hello world",
        "Open notepad and type hello world",
        "Create a folder called test_output",
        "Open quantum computer",  # Should fail
    ]
    
    print(f"\nRunning {len(instructions)} instructions with LIVE LLM...\n")
    
    for i, inst in enumerate(instructions, 1):
        print(f"[{i:2d}] {inst}")
        result = router.process(inst)
        print(f"     → {result['path']} | "
              f"κ: {result['kappa_before']:.4f}→{result['kappa_after']:.4f} | "
              f"Tokens: {result['tokens_used']} | "
              f"Latency: {result['latency_ms']}ms")
        if "phase_transition" in result:
            print(f"     ⚡ TRANSITION: {result['phase_transition']['type']}")
        print()
    
    router.print_status()
    return router


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    import sys
    
    os.makedirs("data", exist_ok=True)
    
    if "--live" in sys.argv:
        # Live mode with real LLM
        backend = "deepseek"
        for arg in sys.argv:
            if arg.startswith("--backend="):
                backend = arg.split("=")[1]
        demo_with_llm(backend)
    else:
        # Simulated mode (no API key needed)
        demo_without_llm()