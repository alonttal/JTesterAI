import argparse
import sys
from pathlib import Path
from executor import TestExecutor
from generator import TestGenerator
from scanner import DependencyScanner
from utils import parse_java_file, analyze_maven_log

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="AI Agent for generating Java Unit Tests")
    parser.add_argument("file", help="Path to the Java source file")
    parser.add_argument("--model", default="qwen2.5-coder", help="Ollama model to use")
    parser.add_argument("--retries", type=int, default=3, help="Max retry attempts")

    args = parser.parse_args()

    target_file = Path(args.file)
    if not target_file.exists():
        print(f"❌ Error: File not found: {target_file}")
        sys.exit(1)

    print(f"📂 Analyzing: {target_file.name}...")

    try:
        # Using the imported function
        package_name, class_name, source_code = parse_java_file(target_file)
        print(f"   > Class: {class_name}")
        print(f"   > Package: {package_name}")
    except ValueError as e:
        print(f"❌ Error parsing file: {e}")
        sys.exit(1)

    # Initialize Components
    executor = TestExecutor()
    generator = TestGenerator(model=args.model)
    scanner = DependencyScanner()

    print("🔎 Scanning dependencies for context...")
    dep_context = scanner.get_dependency_context(source_code, package_name)

    current_test_code = None
    error_log = None

    # --- Agent Loop ---
    for attempt in range(1, args.retries + 1):
        print(f"\n--- 🔄 Attempt {attempt}/{args.retries} ---")

        if attempt == 1:
            current_test_code = generator.generate_test(class_name, source_code, dep_context)
        else:
            print("💡 Step 1: Analyzing previous failure...")

            # 1. Get the Explanation
            analysis = generator.analyze_error(
                class_name,
                source_code,
                current_test_code,
                error_log,
                dep_context
            )
            print(f"   > Diagnosis: {analysis[:200]}...")  # Preview diagnosis

            print("💡 Step 2: Generating fix based on diagnosis...")

            # 2. Generate Code using the Explanation
            current_test_code = generator.apply_fix(
                class_name,
                source_code,
                current_test_code,
                error_log,
                analysis,
                dep_context
            )

        if not current_test_code:
            print("❌ Failed to generate code.")
            break

        test_class_name = class_name + "Test"
        executor.write_test_file(test_class_name, package_name, current_test_code)

        print("⏳ Running Maven test...")
        success, output = executor.run_maven_test(class_name + "Test")

        analysis = analyze_maven_log(output, test_class_name)

        if analysis["is_success"]:
            print(f"\n🎉 SUCCESS! Test passed.")
            return

        if analysis["unrelated_errors"]:
            print("\n⛔ CRITICAL STOP: Unrelated Compilation Errors Detected!")
            print("The agent cannot run tests because other files in your project are broken:")
            for bad_file in analysis["unrelated_errors"]:
                print(f"   > {bad_file}")
            print("\nAction: Please fix these files and try again.")
            sys.exit(1)  # Stop the agent immediately

        # If we got here, the errors are definitely in OUR generated test
        print(f"⚠️ Test Failed (Relevant Errors):")
        print(analysis["relevant_errors"])

        # Pass ONLY the relevant errors to the LLM for the next attempt
        error_log = analysis["relevant_errors"]

    print(f"\n❌ Failed after {args.retries} attempts.")

if __name__ == "__main__":
    main()