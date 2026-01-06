import re


def parse_java_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    package_match = re.search(r"package\s+([\w\.]+);", content)
    if not package_match:
        raise ValueError("Could not find 'package' declaration.")
    package_name = package_match.group(1)

    class_match = re.search(r"public\s+(?:abstract\s+)?(?:class|interface)\s+(\w+)", content)
    if not class_match:
        raise ValueError("Could not find 'public class' declaration.")
    class_name = class_match.group(1)

    return package_name, class_name, content


def analyze_maven_log(log_output, target_test_class):
    lines = log_output.splitlines()
    relevant_errors = []
    seen_errors = set()
    unrelated_errors = set()

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- 1. Catch Compilation Errors ---
        if "[ERROR]" in line and ".java:[" in line:
            match = re.search(r"[/\\]?(\w+\.java):\[(\d+),\d+\]\s+(.*)", line)
            if match:
                file_name = match.group(1)
                line_num = match.group(2)
                main_msg = match.group(3)

                if file_name == f"{target_test_class}.java":
                    full_error = f"Line {line_num}: {main_msg}"

                    # Look Ahead for details
                    j = i + 1
                    details = []
                    while j < len(lines):
                        next_line = lines[j]
                        # Stop if we hit a new error block or info block
                        if ".java:[" in next_line or "[INFO]" in next_line:
                            break

                        if "[ERROR]" in next_line:
                            clean_detail = next_line.replace("[ERROR]", "").strip()
                            if clean_detail.startswith("symbol:") or clean_detail.startswith("location:"):
                                details.append(clean_detail)
                        j += 1

                    if details:
                        full_error += "\n      " + "\n      ".join(details)

                    # Deduplicate
                    if full_error not in seen_errors:
                        relevant_errors.append(full_error)
                        seen_errors.add(full_error)

                    i = j - 1
                else:
                    unrelated_errors.add(file_name)

        # --- 2. Catch Runtime Failures ---
        elif "<<< FAILURE!" in line or "<<< ERROR!" in line:
            clean_header = line.replace("[ERROR]", "").strip()
            if clean_header not in seen_errors:
                relevant_errors.append(f"❌ {clean_header}")
                seen_errors.add(clean_header)

            j = i + 1
            stack_lines = 0
            while j < len(lines) and stack_lines < 20:
                next_line = lines[j]
                if "[INFO] Running" in next_line or "[INFO] Results:" in next_line:
                    break
                if "[INFO]" not in next_line:
                    clean_trace = next_line.replace("[ERROR]", "").strip()
                    relevant_errors.append(f"   {clean_trace}")
                j += 1
                stack_lines += 1

            i = j - 1

        i += 1

    return {
        "relevant_errors": "\n".join(relevant_errors),
        "unrelated_errors": list(unrelated_errors),
        "is_success": "BUILD SUCCESS" in log_output
    }