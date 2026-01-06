import subprocess
from pathlib import Path


class TestExecutor:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()

    def write_test_file(self, class_name, package_name, code_content):
        """
        Writes the generated test code to src/test/java/...
        """
        # Convert package (com.example) to path (com/example)
        package_path = package_name.replace(".", "/")
        target_dir = self.project_root / "src/test/java" / package_path
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{class_name}.java"

        print(f"📝 Writing test file to: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)

        return file_path

    def run_maven_test(self, test_class_name):
        """
        Runs 'mvn test' specifically for the generated class.
        Returns: (success: bool, output: str)
        """
        # Maven command to run a specific test class
        # -Dtest=MyTestClass
        cmd = ["mvn", "test", f"-Dtest={test_class_name}"]

        print(f"🚀 Running command: {' '.join(cmd)}")

        try:
            # Capture both stdout and stderr
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False  # Don't throw exception on failure, we want to read the logs
            )

            success = result.returncode == 0
            output = result.stdout + "\n" + result.stderr
            return success, output

        except FileNotFoundError:
            return False, "❌ Error: 'mvn' command not found. Is Maven installed and in your PATH?"


# --- Smoke Test (Run this file directly to test the harness) ---
if __name__ == "__main__":
    # 1. Initialize
    executor = TestExecutor()

    # 2. Define a dummy test (intentionally failing to see if we catch it)
    dummy_code = """
    package com.example;

    import org.junit.jupiter.api.Test;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    public class AgentSmokeTest {
        @Test
        public void testVerifyExecutor() {
            System.out.println("--- AGENT SMOKE TEST RUNNING ---");
            assertTrue(true, "This should pass");
        }
    }
    """

    # 3. Write it
    print("--- 1. Testing Write ---")
    executor.write_test_file("AgentSmokeTest", "com.example", dummy_code)

    # 4. Run it
    print("\n--- 2. Testing Execution ---")
    success, log = executor.run_maven_test("AgentSmokeTest")

    print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    if "--- AGENT SMOKE TEST RUNNING ---" in log:
        print("Confirmed: Maven actually ran our code.")
    else:
        print("Warning: Did not see expected output in logs.")
