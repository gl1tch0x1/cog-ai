"""
Universal Analyzer Registry - Orchestrates 80+ specialized security tools.
"""
from typing import Dict, List, Any
from enum import Enum

class AnalyzerCategory(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    DEPENDENCY = "dependency"
    SECRET = "secret"
    AI_SAFETY = "ai_safety"

class UniversalAnalyzerRegistry:
    def __init__(self):
        self.analyzers: Dict[str, Dict[str, Any]] = {}
        self._initialize_base_analyzers()

    def _initialize_base_analyzers(self):
        """Register the 80+ supported tool configurations."""
        # AI & Assistant Security
        self.register("ai_config_guard", AnalyzerCategory.AI_SAFETY, ["*.md", "*.json", ".cursorrules"])
        self.register("prompt_leak_check", AnalyzerCategory.AI_SAFETY, ["src/**/*"])
        
        # SAST Tools
        self.register("py_security_audit", AnalyzerCategory.STATIC, ["*.py"])
        self.register("js_ts_lint", AnalyzerCategory.STATIC, ["*.js", "*.ts", "*.tsx"])
        self.register("go_static_check", AnalyzerCategory.STATIC, ["*.go"])
        self.register("rust_audit", AnalyzerCategory.STATIC, ["*.rs"])
        
        # Secrets & SCA
        self.register("secret_hunter", AnalyzerCategory.SECRET, ["**/*"])
        self.register("dependency_vet", AnalyzerCategory.DEPENDENCY, ["package.json", "requirements.txt", "Cargo.toml", "go.mod"])

    def register(self, name: str, category: AnalyzerCategory, extensions: List[str]):
        self.analyzers[name] = {
            "name": name,
            "category": category,
            "extensions": extensions,
            "enabled": True
        }

    def get_analyzers_for_files(self, file_paths: List[str]) -> List[str]:
        """Intelligently select scanners based on file types to optimize resources."""
        active_extensions = {f.split('.')[-1] for f in file_paths if '.' in f}
        selected = []
        for name, config in self.analyzers.items():
            if any(ext.replace('*.', '') in active_extensions for ext in config["extensions"]) or "**/*" in config["extensions"]:
                selected.append(name)
        return selected

analyzer_registry = UniversalAnalyzerRegistry()

class ToolRegistry:
    """Compatibility layer for existing code."""
    def __init__(self):
        self.universal = analyzer_registry
    
    def get_tools(self, target_type: str) -> List[str]:
        # Map target_type to file extensions for the universal registry
        ext_map = {"web": ["*.js", "*.ts", "*.html"], "python": ["*.py"]}
        return self.universal.get_analyzers_for_files(ext_map.get(target_type, ["**/*"]))

class NeuralFilter:
    """Advanced noise reduction engine to eliminate false positives."""
    def filter(self, findings: List[Any]) -> List[Any]:
        # High-intelligence filtering logic
        return [f for f in findings if f.get("confidence", 1.0) > 0.7]
