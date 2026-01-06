import os
import re
from pathlib import Path


class DependencyScanner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        # Common Java/SDK types to ignore to save time/context
        self.ignored_types = {
            "String", "Integer", "Long", "Double", "Boolean", "List", "Map", "Set",
            "Optional", "Object", "Class", "System", "Logger", "Arrays", "Collections"
        }

    def get_dependency_context(self, source_code, current_package_name):
        """
        Analyzes source code for BOTH explicit imports and same-package implicit deps.
        """
        context_str = ""
        found_files = set()  # Track what we've already scanned to avoid duplicates

        # 1. Explicit Imports
        imports = self._extract_imports(source_code)

        # 2. Same-Package Implicit Dependencies
        same_pkg_deps = self._scan_same_package_deps(source_code, current_package_name)

        # Combine all candidates
        all_candidates = imports + same_pkg_deps

        print(f"🔎 Scanning dependencies...")

        for class_name, package_name in all_candidates:
            # Skip standard libraries
            if package_name.startswith(("java.", "javax.", "org.junit.", "org.mockito.")):
                continue

            # Skip if we already processed this class
            if class_name in found_files:
                continue

            file_path = self._find_file(class_name, package_name)

            if file_path and file_path.exists():
                print(f"   > Found dependency: {class_name} ({file_path.name})")
                signatures = self._extract_public_signatures(file_path)
                context_str += f"\n--- Dependency: {class_name} ---\n{signatures}\n"
                found_files.add(class_name)

        return context_str

    def _extract_imports(self, source_code):
        """ Returns list of (ClassName, PackageName) from 'import' statements """
        pattern = r"import\s+([\w\.]+)\.([A-Z]\w+);"
        matches = re.findall(pattern, source_code)
        return [(m[1], m[0]) for m in matches]

    def _scan_same_package_deps(self, source_code, current_package):
        """
        Scans for capitalized words used as types (fields, args)
        that likely belong to the same package.
        """
        # Regex to find types in declarations:
        # e.g., "private UserRepo repo;" -> matches "UserRepo"
        # e.g., "public Service(Helper h)" -> matches "Helper"

        # Look for capitalized words that are NOT keywords
        # This is a heuristic: match "Type variable" pattern
        pattern = r"\b([A-Z][a-zA-Z0-9]*)\s+[a-z][a-zA-Z0-9]*\b"

        potential_matches = re.findall(pattern, source_code)

        candidates = []
        for class_name in set(potential_matches):
            if class_name not in self.ignored_types:
                # Assume it belongs to the current package
                candidates.append((class_name, current_package))

        return candidates

    def _find_file(self, class_name, package_name):
        path_suffix = package_name.replace(".", "/")
        possible_roots = [
            self.project_root / "src/main/java",
            self.project_root / "src/test/java"
        ]

        for root in possible_roots:
            full_path = root / path_suffix / f"{class_name}.java"
            if full_path.exists():
                return full_path
        return None

    def _extract_public_signatures(self, file_path):
        signatures = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("public") and "class " not in stripped and "interface " not in stripped:
                        clean_sig = stripped.split("{")[0].strip() + ";"
                        signatures.append(clean_sig)
        except Exception:
            return ""
        return "\n".join(signatures)


# --- Smoke Test ---
if __name__ == "__main__":
    # Setup dummy environment
    test_pkg_dir = Path("src/main/java/com/dummy")
    test_pkg_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a neighbor class (Same Package, No Import)
    with open(test_pkg_dir / "Neighbor.java", "w") as f:
        f.write("""
        package com.dummy;
        public class Neighbor {
            public int getValue() { return 42; }
        }
        """)

    # 2. Source code that uses Neighbor (implicitly)
    source = """
    package com.dummy;
    public class MainService {
        private Neighbor neighbor; // <--- Implicit dependency
        public MainService(Neighbor n) { this.neighbor = n; }
    }
    """

    scanner = DependencyScanner()
    # Pass the package explicitly
    print(scanner.get_dependency_context(source, "com.dummy"))