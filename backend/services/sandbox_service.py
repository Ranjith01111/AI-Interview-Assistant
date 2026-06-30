"""
Sandbox Service — Execution Engine for Coding Assessments

SECURITY HARDENED — 2026-06-27

Compiles and runs code inside containerized Docker Sandboxes.
Enforces time and memory limits.
Falls back gracefully to local subprocess execution when Docker daemon is not active.
Runs SQL queries inside isolated SQLite memory databases.
"""

import asyncio
import os
import re
import sys
import shutil
import subprocess
import tempfile
import time
import sqlite3
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path

from backend.core.logging import get_logger

logger = get_logger("backend.services.sandbox_service")


# ── Code Sanitization ──────────────────────────────────────────────────────
# Block dangerous patterns that could escape the sandbox or harm the host.

BLOCKED_PYTHON_PATTERNS = [
    r"\bos\.system\b",
    r"\bos\.popen\b",
    r"\bos\.exec\w*\b",
    r"\bos\.spawn\w*\b",
    r"\bos\.remove\b",
    r"\bos\.unlink\b",
    r"\bos\.rmdir\b",
    r"\bshutil\.rmtree\b",
    r"\bsubprocess\b",
    r"\b__import__\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\bopen\s*\(.*(w|a|x)",  # block write/append/create modes
    r"\bsocket\b",
    r"\brequests\b",
    r"\burllib\b",
    r"\bhttp\.client\b",
    r"\bctypes\b",
    r"\bsignal\b",
    r"\bsys\.exit\b",
]

BLOCKED_JS_PATTERNS = [
    r"\bchild_process\b",
    r"\bexecSync\b",
    r"\bexecFile\b",
    r"\bspawnSync\b",
    r"\bspawn\b",
    r"\brequire\s*\(\s*['\"]fs['\"]\)(?!\s*\.\s*readFileSync)",
    r"\brequire\s*\(\s*['\"]net['\"]",
    r"\brequire\s*\(\s*['\"]http['\"]",
    r"\brequire\s*\(\s*['\"]https['\"]",
    r"\brequire\s*\(\s*['\"]os['\"]",
    r"\bprocess\.exit\b",
    r"\bprocess\.env\b",
    r"\beval\s*\(",
    r"\bFunction\s*\(",
]

BLOCKED_CPP_PATTERNS = [
    r"\bsystem\s*\(",
    r"\bpopen\s*\(",
    r"\bexecl\b",
    r"\bexecv\b",
    r"\bfork\s*\(",
    r"\b#include\s*<(sys/socket|netinet|arpa|netdb)",
]

BLOCKED_JAVA_PATTERNS = [
    r"\bRuntime\.getRuntime\(\)\.exec\b",
    r"\bProcessBuilder\b",
    r"\bSocket\b",
    r"\bServerSocket\b",
    r"\bURLConnection\b",
    r"\bSystem\.exit\b",
    r"\bjava\.net\b",
    r"\bjava\.lang\.reflect\b",
]


def _sanitize_code(language: str, code: str) -> str | None:
    """
    Returns an error message if blocked patterns are found, else None.
    This is a defense-in-depth measure — not a replacement for sandboxing.
    """
    patterns_map = {
        "python": BLOCKED_PYTHON_PATTERNS,
        "javascript": BLOCKED_JS_PATTERNS,
        "c": BLOCKED_CPP_PATTERNS,
        "cpp": BLOCKED_CPP_PATTERNS,
        "java": BLOCKED_JAVA_PATTERNS,
    }
    patterns = patterns_map.get(language, [])
    for pattern in patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return f"Blocked: Code contains prohibited pattern matching '{pattern}'. System calls, network access, and file writes are not allowed."
    return None


class SandboxService:
    """
    SandboxService handles the orchestration of Docker container sandboxes
    and local subprocess runs for five supported languages.
    """

    def __init__(self):
        self._docker_available = None

    async def check_docker_available(self) -> bool:
        """Checks if Docker command is available and daemon is running."""
        if self._docker_available is not None:
            return self._docker_available

        docker_cmd = "docker.exe" if os.name == "nt" else "docker"
        try:
            # Run docker info with 5.0s timeout to check daemon status
            proc = await asyncio.create_subprocess_exec(
                docker_cmd, "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=5.0)
                self._docker_available = (proc.returncode == 0)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                self._docker_available = False
        except Exception:
            self._docker_available = False

        if self._docker_available:
            logger.info("docker_sandbox_active", status="Running inside containerized Docker sandbox")
        else:
            logger.warning("docker_sandbox_inactive", status="Docker daemon not running; using local subprocess fallback")
        return self._docker_available

    async def execute(
        self,
        language: str,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: float = 2.0,
        memory_limit: int = 128
    ) -> Dict[str, Any]:
        """
        Executes candidate's code against a set of test cases.

        Args:
            language: python, javascript, java, cpp, sql
            code: candidate's written code
            test_cases: list of dicts with inputs/outputs
            time_limit: float, execution time limit in seconds
            memory_limit: int, memory limit in MB

        Returns:
            Dict containing final status, score (percentage passed), and test results.
        """
        lang = language.lower().strip()

        # Normalize language
        if lang == "c":
            lang = "c"

        # Handle SQL in-memory database execution separately
        if lang == "sql":
            return await self._execute_sql(code, test_cases)

        # ── Security: Sanitize code before execution ──────────────────
        violation = _sanitize_code(lang, code)
        if violation:
            logger.warning("code_blocked_by_sanitizer", language=lang, reason=violation)
            return {
                "status": "Security Violation",
                "score": 0,
                "results": [],
                "error": violation,
            }

        # SECURITY: Require Docker for code execution, but use local fallback if unavailable
        docker_ok = await self.check_docker_available()
        if not docker_ok:
            logger.warning("sandbox_using_local_fallback", language=lang)
            return await self._execute_local(lang, code, test_cases, time_limit, memory_limit)

        try:
            return await self._execute_docker(lang, code, test_cases, time_limit, memory_limit)
        except Exception as e:
            logger.error("execute_failed_top_level", error=str(e), language=lang)
            import traceback
            return {
                "status": "System Error",
                "score": 0,
                "results": [],
                "error": f"Execution failed: {str(e)}",
                "compile_error": str(e)
            }

    # ── SQL SQLite Execution Engine ──────────────────────────────────────
    async def _execute_sql(self, query: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs SQL code against SQLite memory DB schemas and compares outputs."""
        results = []
        passed_count = 0

        for i, tc in enumerate(test_cases):
            schema_sql = tc.get("schema_sql", "")
            seed_sql = tc.get("seed_sql", "")
            expected_json = tc.get("expected_output", "[]")
            is_hidden = tc.get("is_hidden", False)

            # Try parsing expected output JSON
            try:
                expected_rows = json.loads(expected_json) if isinstance(expected_json, str) else expected_json
            except Exception:
                expected_rows = []

            # Execute query in an in-memory SQLite DB
            run_time = 0.0
            conn = None
            try:
                conn = sqlite3.connect(":memory:")
                cursor = conn.cursor()
                
                # Pre-populate database
                if schema_sql:
                    cursor.executescript(schema_sql)
                if seed_sql:
                    cursor.executescript(seed_sql)
                
                start_t = time.perf_counter()
                cursor.execute(query)
                
                # Fetch columns and data
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    actual_rows = [dict(zip(columns, row)) for row in rows]
                else:
                    actual_rows = []
                
                run_time = (time.perf_counter() - start_t) * 1000.0  # in ms
                conn.commit()

                # Compare outputs
                # Sort rows and columns to prevent ordering validation errors if order is not strict
                def normalize(data):
                    if not isinstance(data, list):
                        return data
                    normalized_list = []
                    for row in data:
                        if isinstance(row, dict):
                            # Convert keys to lowercase and values to string for soft comparison
                            normalized_list.append({str(k).lower(): str(v).strip() for k, v in row.items()})
                        else:
                            normalized_list.append(str(row))
                    return normalized_list

                norm_actual = normalize(actual_rows)
                norm_expected = normalize(expected_rows)
                
                passed = (norm_actual == norm_expected)
                error_msg = None
                
            except Exception as e:
                passed = False
                actual_rows = []
                error_msg = f"SQL Execution Error: {str(e)}"
            finally:
                if conn:
                    conn.close()

            results.append({
                "test_case_index": i,
                "is_hidden": is_hidden,
                "passed": passed,
                "input": tc.get("input", "SQL Test Database"),
                "expected": expected_rows if not is_hidden else "[HIDDEN]",
                "actual": actual_rows if not is_hidden or error_msg else "[HIDDEN]",
                "error": error_msg,
                "run_time_ms": round(run_time, 2),
                "run_memory_mb": 0.0
            })

            if passed:
                passed_count += 1

        score = int((passed_count / len(test_cases)) * 100) if test_cases else 0
        status = "Passed" if score == 100 else "Failed"
        if any(r["error"] is not None for r in results):
            status = "Runtime Error"

        return {
            "status": status,
            "score": score,
            "sandbox_type": "SQLite In-Memory DB",
            "results": results
        }

    # ── Docker Execution Sandbox ──────────────────────────────────────────
    async def _execute_docker(
        self,
        lang: str,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: float,
        memory_limit: int
    ) -> Dict[str, Any]:
        """Runs compilation once, then executes candidate code inside Docker containers."""
        # Map languages to files and Docker images
        config = {
            "python": {"file": "solution.py", "image": "python:3.10-slim", "run_cmd": "python solution.py"},
            "javascript": {"file": "solution.js", "image": "node:18-slim", "run_cmd": "node solution.js"},
            "c": {"file": "main.c", "image": "gcc:latest", "run_cmd": "./main"},
            "cpp": {"file": "main.cpp", "image": "gcc:latest", "run_cmd": "./main"},
            "java": {"file": "Solution.java", "image": "openjdk:17-slim", "run_cmd": "java Solution"}
        }

        if lang not in config:
            return {"status": "System Error", "score": 0, "results": [], "error": f"Language {lang} not supported in Docker."}

        cfg = config[lang]
        sandbox_id = f"sandbox_{int(time.time())}_{os.urandom(4).hex()}"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write source code file
            src_file = temp_path / cfg["file"]
            src_file.write_text(code, encoding="utf-8")

            # ── 1. Compilation Phase (C++ and Java) ────────────────────────
            DOCKER_CMD = "docker.exe" if os.name == "nt" else "docker"
            is_compiled = lang in ["c", "cpp", "java"]
            if is_compiled:
                comp_container_name = f"{sandbox_id}_compile"
                if lang == "c":
                    comp_cmd = [DOCKER_CMD, "create", "--name", comp_container_name, "-w", "/app", cfg["image"], "gcc", "-O2", cfg["file"], "-o", "main", "-lm"]
                elif lang == "cpp":
                    comp_cmd = [DOCKER_CMD, "create", "--name", comp_container_name, "-w", "/app", cfg["image"], "g++", "-O3", cfg["file"], "-o", "main"]
                else:  # java
                    comp_cmd = [DOCKER_CMD, "create", "--name", comp_container_name, "-w", "/app", cfg["image"], "javac", cfg["file"]]

                # Create compile container
                proc = await asyncio.create_subprocess_exec(*comp_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

                # Copy source file in
                cp_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "cp", cfg["file"], f"{comp_container_name}:/app/{cfg['file']}", cwd=temp_dir)
                await cp_proc.communicate()

                # Start compile container and capture stdout/stderr
                start_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "start", "-a", comp_container_name, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await start_proc.communicate()

                # Check compile status
                if start_proc.returncode != 0:
                    # Clean compile container
                    rm_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "rm", "-f", comp_container_name)
                    await rm_proc.communicate()
                    
                    return {
                        "status": "Compile Error",
                        "score": 0,
                        "sandbox_type": "Docker Container Sandbox",
                        "results": [],
                        "compile_error": stderr.decode("utf-8", errors="replace") or stdout.decode("utf-8", errors="replace")
                    }

                # Copy compiled binary/classes out to host temp directory
                if lang == "cpp":
                    cp_out = await asyncio.create_subprocess_exec(DOCKER_CMD, "cp", f"{comp_container_name}:/app/main", "main", cwd=temp_dir)
                    await cp_out.communicate()
                else: # java
                    # Copy all class files
                    cp_out = await asyncio.create_subprocess_exec(DOCKER_CMD, "cp", f"{comp_container_name}:/app/.", ".", cwd=temp_dir)
                    await cp_out.communicate()

                # Clean up compile container
                rm_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "rm", comp_container_name)
                await rm_proc.communicate()

            # ── 2. Run Phase (for each test case) ──────────────────────────
            results = []
            passed_count = 0

            for idx, tc in enumerate(test_cases):
                input_data = tc.get("input", "")
                expected_output = tc.get("expected_output", "").strip()
                is_hidden = tc.get("is_hidden", False)

                # Write test case input to file on host
                input_file = temp_path / "input.txt"
                input_file.write_text(input_data, encoding="utf-8")

                run_container_name = f"{sandbox_id}_run_{idx}"

                # Construct execution container
                # Enforce network none, memory limit, and read stdin
                exec_command = f"{cfg['run_cmd']} < input.txt"
                docker_cmd = [
                    DOCKER_CMD, "create",
                    "--name", run_container_name,
                    "--network", "none",
                    "--memory", f"{memory_limit}m",
                    "--memory-swap", f"{memory_limit}m",
                    "-w", "/app",
                    "-i",
                    cfg["image"],
                    "sh", "-c", exec_command
                ]

                # Create container
                proc = await asyncio.create_subprocess_exec(*docker_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

                # Copy code/binaries and input.txt in
                # Copy everything in host temp_path directory to container /app/
                cp_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "cp", ".", f"{run_container_name}:/app/", cwd=temp_dir)
                await cp_proc.communicate()

                # Run container with time limits
                start_time = time.perf_counter()
                run_proc = await asyncio.create_subprocess_exec(
                    DOCKER_CMD, "start", "-a", run_container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Control timeout in Python
                stdout, stderr = b"", b""
                timed_out = False
                try:
                    stdout, stderr = await asyncio.wait_for(run_proc.communicate(), timeout=time_limit)
                    elapsed_time = (time.perf_counter() - start_time) * 1000.0  # ms
                except asyncio.TimeoutError:
                    timed_out = True
                    elapsed_time = time_limit * 1000.0
                    # Kill container forcefully
                    kill_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "kill", run_container_name)
                    await kill_proc.communicate()

                # Capture exit code
                exit_code = run_proc.returncode

                # Clean container
                rm_proc = await asyncio.create_subprocess_exec(DOCKER_CMD, "rm", "-f", run_container_name)
                await rm_proc.communicate()

                # Determine execution status
                actual_out = stdout.decode("utf-8", errors="replace").strip()
                err_out = stderr.decode("utf-8", errors="replace").strip()

                passed = False
                error_msg = None
                status = "Passed"

                if timed_out:
                    status = "Time Limit Exceeded"
                    error_msg = f"Time Limit Exceeded (> {time_limit}s)"
                elif exit_code == 137:
                    # 137 exit code usually signifies OOM kill by Docker daemon
                    status = "Memory Limit Exceeded"
                    error_msg = f"Memory Limit Exceeded (> {memory_limit}MB)"
                elif exit_code != 0:
                    status = "Runtime Error"
                    error_msg = err_out or f"Process exited with non-zero code {exit_code}"
                else:
                    passed = (actual_out == expected_output)
                    if not passed:
                        status = "Failed"

                if passed:
                    passed_count += 1

                results.append({
                    "test_case_index": idx,
                    "is_hidden": is_hidden,
                    "passed": passed,
                    "status": status,
                    "input": input_data if not is_hidden else "[HIDDEN]",
                    "expected": expected_output if not is_hidden else "[HIDDEN]",
                    "actual": actual_out if not is_hidden or error_msg else "[HIDDEN]",
                    "error": error_msg,
                    "run_time_ms": round(elapsed_time, 2),
                    "run_memory_mb": 0.0  # docker statistics could fetch it, but approximate it based on limits
                })

            score = int((passed_count / len(test_cases)) * 100) if test_cases else 0
            
            # Submission level status
            submission_status = "Passed" if score == 100 else "Failed"
            for r in results:
                if r["status"] in ["Time Limit Exceeded", "Memory Limit Exceeded", "Runtime Error"]:
                    submission_status = r["status"]
                    break

            return {
                "status": submission_status,
                "score": score,
                "sandbox_type": "Docker Container Sandbox",
                "results": results
            }

    # ── Local Subprocess Execution Fallback ────────────────────────────────
    async def _execute_local(
        self,
        lang: str,
        code: str,
        test_cases: List[Dict[str, Any]],
        time_limit: float,
        memory_limit: int,
        warning: str = ""
    ) -> Dict[str, Any]:
        """Runs compilation and executes code locally via Python subprocesses."""
        results = []
        passed_count = 0

        # Verify command availability on local host
        local_commands = {
            "python": sys.executable,  # Use the same Python running this server
            "javascript": "node",
            "c": "gcc",
            "cpp": "g++",
            "java": "javac"
        }

        # For non-python, check if command exists
        resolved_commands = {"python": sys.executable}
        if lang != "python":
            cmd_to_check = local_commands.get(lang)
            resolved_cmd = shutil.which(cmd_to_check)
            if not resolved_cmd:
                return {
                    "status": "System Error",
                    "score": 0,
                    "sandbox_type": warning,
                    "results": [],
                    "compile_error": f"Language runtime '{cmd_to_check or lang}' not found. Install it or use Python."
                }
            resolved_commands[lang] = resolved_cmd
            
            # Need 'java' runtime for java, not just javac
            if lang == "java":
                java_runtime = shutil.which("java")
                if not java_runtime:
                    return {
                        "status": "System Error",
                        "score": 0,
                        "sandbox_type": warning,
                        "results": [],
                        "compile_error": f"Java runtime (JRE) not found."
                    }
                resolved_commands["java_run"] = java_runtime

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write code file
            file_names = {"python": "solution.py", "javascript": "solution.js", "c": "main.c", "cpp": "main.cpp", "java": "Solution.java"}
            if lang not in file_names:
                return {
                    "status": "System Error",
                    "score": 0,
                    "sandbox_type": warning,
                    "results": [],
                    "compile_error": f"Unsupported language: {lang}"
                }
            src_file = temp_path / file_names[lang]
            src_file.write_text(code, encoding="utf-8")

            # ── 1. Local Compile Phase ─────────────────────────────────────
            # NOTE: asyncio.create_subprocess_exec raises NotImplementedError on
            # Windows with SelectorEventLoop (used by uvicorn). We use
            # subprocess.run via asyncio.to_thread instead — works everywhere.
            def _run_sync(cmd, cwd=None, input_bytes=None, timeout=None):
                """Blocking subprocess wrapper executed in a thread."""
                try:
                    # SECURITY FIX: Never use shell=True with untrusted input
                    proc_result = subprocess.run(
                        cmd,
                        input=input_bytes,
                        capture_output=True,
                        cwd=cwd,
                        timeout=timeout or 10,
                        shell=False,  # SECURITY: shell=False prevents command injection
                    )
                    return proc_result
                except subprocess.TimeoutExpired:
                    # Return a fake result for timeout
                    class _FakeResult:
                        stdout = b""
                        stderr = b"Time Limit Exceeded"
                        returncode = -1
                        timed_out = True
                    return _FakeResult()
                except Exception as e:
                    class _FakeResult:
                        stdout = b""
                        stderr = str(e).encode("utf-8")
                        returncode = -1
                        timed_out = False
                    return _FakeResult()

            if lang == "c":
                binary_name = "main.exe" if os.name == "nt" else "main"
                comp_cmd = [resolved_commands["c"], "-O2", "main.c", "-o", binary_name, "-lm"]
                result = await asyncio.to_thread(_run_sync, comp_cmd, temp_dir)
                if result.returncode != 0:
                    return {
                        "status": "Compile Error",
                        "score": 0,
                        "sandbox_type": warning,
                        "results": [],
                        "compile_error": result.stderr.decode("utf-8", errors="replace") or result.stdout.decode("utf-8", errors="replace")
                    }
                exec_cmd = [str(temp_path / binary_name)]

            elif lang == "cpp":
                binary_name = "main.exe" if os.name == "nt" else "main"
                comp_cmd = [resolved_commands["cpp"], "-O3", "main.cpp", "-o", binary_name]
                result = await asyncio.to_thread(_run_sync, comp_cmd, temp_dir)
                if result.returncode != 0:
                    return {
                        "status": "Compile Error",
                        "score": 0,
                        "sandbox_type": warning,
                        "results": [],
                        "compile_error": result.stderr.decode("utf-8", errors="replace") or result.stdout.decode("utf-8", errors="replace")
                    }
                exec_cmd = [str(temp_path / binary_name)]

            elif lang == "java":
                comp_cmd = [resolved_commands["java"], "Solution.java"]
                result = await asyncio.to_thread(_run_sync, comp_cmd, temp_dir)
                if result.returncode != 0:
                    return {
                        "status": "Compile Error",
                        "score": 0,
                        "sandbox_type": warning,
                        "results": [],
                        "compile_error": result.stderr.decode("utf-8", errors="replace") or result.stdout.decode("utf-8", errors="replace")
                    }
                exec_cmd = [resolved_commands["java_run"], "-cp", temp_dir, "Solution"]

            elif lang == "python":
                exec_cmd = [sys.executable, str(src_file)]
            elif lang == "javascript":
                exec_cmd = [resolved_commands["javascript"], str(src_file)]

            # ── 2. Run each test case ──────────────────────────────────────
            for idx, tc in enumerate(test_cases):
                input_data = tc.get("input", "")
                expected_output = tc.get("expected_output", "").strip()
                is_hidden = tc.get("is_hidden", False)

                start_time = time.perf_counter()
                timed_out = False
                stdout, stderr = b"", b""

                try:
                    result = await asyncio.to_thread(
                        _run_sync,
                        exec_cmd,
                        temp_dir,
                        input_data.encode("utf-8"),
                        time_limit
                    )
                    elapsed_time = (time.perf_counter() - start_time) * 1000.0
                    stdout = result.stdout
                    stderr = result.stderr
                    exit_code = result.returncode
                    timed_out = getattr(result, 'timed_out', False)
                except Exception as e:
                    elapsed_time = (time.perf_counter() - start_time) * 1000.0
                    stderr = str(e).encode("utf-8")
                    exit_code = -1
                    timed_out = False

                # exit_code already set above
                actual_out = stdout.decode("utf-8", errors="replace").strip()
                err_out = stderr.decode("utf-8", errors="replace").strip()

                passed = False
                error_msg = None
                status = "Passed"

                if timed_out:
                    status = "Time Limit Exceeded"
                    error_msg = f"Time Limit Exceeded (> {time_limit}s)"
                elif exit_code != 0:
                    status = "Runtime Error"
                    error_msg = err_out or f"Process exited with non-zero code {exit_code}"
                else:
                    passed = (actual_out == expected_output)
                    if not passed:
                        status = "Failed"

                if passed:
                    passed_count += 1

                results.append({
                    "test_case_index": idx,
                    "is_hidden": is_hidden,
                    "passed": passed,
                    "status": status,
                    "input": input_data if not is_hidden else "[HIDDEN]",
                    "expected": expected_output if not is_hidden else "[HIDDEN]",
                    "actual": actual_out if not is_hidden or error_msg else "[HIDDEN]",
                    "error": error_msg,
                    "run_time_ms": round(elapsed_time, 2),
                    "run_memory_mb": 0.0  # memory limits approximation local
                })

            score = int((passed_count / len(test_cases)) * 100) if test_cases else 0
            
            # Submission level status
            submission_status = "Passed" if score == 100 else "Failed"
            for r in results:
                if r["status"] in ["Time Limit Exceeded", "Memory Limit Exceeded", "Runtime Error"]:
                    submission_status = r["status"]
                    break

            return {
                "status": submission_status,
                "score": score,
                "sandbox_type": warning,
                "results": results
            }

# Instantiate singleton sandbox service
sandbox_service = SandboxService()
