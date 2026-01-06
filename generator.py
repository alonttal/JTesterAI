import ollama
import re


class TestGenerator:
    def __init__(self, model="qwen2.5-coder"):
        self.model = model

        # 1. Generator Persona
        self.system_prompt_generate = """
        You are an expert Java QA Automation Engineer.
        Your goal is to write robust JUnit 5 tests.
        OUTPUT ONLY JAVA CODE. No conversational text.
        """

        # 2. Analyst Persona (Pure Text)
        self.system_prompt_analyze = """
        You are a Senior Java Developer reviewing a failed test.
        Your goal is to diagnose the root cause of the failure based on the logs.
        Be concise and technical. Do not write code yet.
        """

    def generate_test(self, class_name, source_code, dependency_context=""):
        user_prompt = f"""
        Write a unit test class for: {class_name}

        SOURCE CODE:
        ```java
        {source_code}
        ```

        CONTEXT (Dependencies):
        ```text
        {dependency_context}
        ```

        Remember:
        1. Use JUnit 5 and Mockito.
        2. Package name must match the source.
        3. Output ONLY the Java code block.
        """
        print(f"🧠 Generating initial test... (Model: {self.model})")
        return self._call_ollama(self.system_prompt_generate, user_prompt, extract_code=True)

    # --- STEP 1: REASONING ---
    def analyze_error(self, class_name, source_code, current_test_code, error_log, dependency_context):
        user_prompt = f"""
        The test for {class_name} failed. Analyze the error log and explain the fix.

        SOURCE CODE:
        ```java
        {source_code}
        ```

        FAILED TEST CODE:
        ```java
        {current_test_code}
        ```

        ERROR LOG:
        ```text
        {error_log}
        ```

        CONTEXT (Dependencies):
        ```text
        {dependency_context}
        ```

        INSTRUCTIONS:
        1. Identify the specific compilation error or assertion failure.
        2. Explain specifically what needs to change in the test code (e.g., "Add import for X", "Change mock return type to Y").
        3. Do NOT output the full code yet. Just the analysis.
        """
        print(f"🕵️ Analyzing failure... (Model: {self.model})")
        # We want raw text here, not code extraction
        return self._call_ollama(self.system_prompt_analyze, user_prompt, extract_code=False)

    # --- STEP 2: CODING ---
    def apply_fix(self, class_name, source_code, current_test_code, error_log, analysis, dependency_context):
        user_prompt = f"""
        Fix the failed Java test based on your analysis.

        YOUR ANALYSIS:
        "{analysis}"

        ERROR LOG:
        ```text
        {error_log}
        ```

        FAILED TEST CODE:
        ```java
        {current_test_code}
        ```

        SOURCE CODE:
        ```java
        {source_code}
        ```

        CONTEXT (Dependencies):
        ```text
        {dependency_context}
        ```

        Output the FULL corrected {class_name}Test.java class.
        """
        print(f"🔧 Applying fix... (Model: {self.model})")
        return self._call_ollama(self.system_prompt_generate, user_prompt, extract_code=True)

    def _call_ollama(self, system_prompt, user_prompt, extract_code=True):
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ])

            content = response['message']['content']
            if extract_code:
                return self._extract_code(content)
            return content.strip()

        except Exception as e:
            print(f"❌ Error communicating with Ollama: {e}")
            return None

    def _extract_code(self, raw_text):
        pattern = r"```java\s*(.*?)\s*```"
        match = re.search(pattern, raw_text, re.DOTALL)
        if match:
            return match.group(1).strip()

        pattern_generic = r"```\s*(.*?)\s*```"
        match_generic = re.search(pattern_generic, raw_text, re.DOTALL)
        if match_generic:
            return match_generic.group(1).strip()

        return raw_text.strip()  # Fallback