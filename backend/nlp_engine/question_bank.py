"""
Question Bank — 500+ interview question templates organized by technology, category, and difficulty.

Each question includes expected keywords for automated answer evaluation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random


@dataclass
class Question:
    """A single interview question template."""
    id: str
    text: str
    topic: str
    difficulty: str  # easy, medium, hard
    category: str  # python, javascript, react, sql, aws, docker, ml, system_design, etc.
    question_type: str  # technical, hr, behavioral
    expected_keywords: List[str] = field(default_factory=list)
    model_answer_hint: str = ""
    follow_up: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON QUESTIONS (50)
# ═══════════════════════════════════════════════════════════════════════════════

PYTHON_QUESTIONS = [
    # --- EASY (15) ---
    Question(
        id="py_001", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What are the main differences between a Python list and a tuple?",
        expected_keywords=["mutable", "immutable", "list", "tuple", "ordered", "index", "append", "performance", "hashable"],
        model_answer_hint="Lists are mutable (can be modified after creation), while tuples are immutable. Tuples are hashable and can be used as dictionary keys. Tuples have slightly better performance due to immutability.",
    ),
    Question(
        id="py_002", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="Explain the difference between '==' and 'is' in Python.",
        expected_keywords=["equality", "identity", "value", "object", "memory", "reference", "id", "compare"],
        model_answer_hint="'==' checks value equality (whether two objects have the same value), while 'is' checks identity (whether two references point to the same object in memory).",
    ),
    Question(
        id="py_003", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What is a Python dictionary and how does it work internally?",
        expected_keywords=["key-value", "hash", "hash table", "lookup", "O(1)", "mutable", "unordered", "collision"],
        model_answer_hint="A dictionary is a key-value mapping implemented as a hash table. Keys must be hashable. Lookups are O(1) average case. Python handles hash collisions using open addressing.",
    ),
    Question(
        id="py_004", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What are *args and **kwargs in Python?",
        expected_keywords=["variable", "arguments", "positional", "keyword", "tuple", "dictionary", "unpacking", "flexible"],
        model_answer_hint="*args collects extra positional arguments into a tuple. **kwargs collects extra keyword arguments into a dictionary. They allow functions to accept variable numbers of arguments.",
    ),
    Question(
        id="py_005", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="Explain list comprehension in Python with an example.",
        expected_keywords=["concise", "loop", "filter", "expression", "iterable", "readable", "one-line", "conditional"],
        model_answer_hint="List comprehensions provide a concise way to create lists using a single line: [expression for item in iterable if condition]. They are more readable and often faster than equivalent for loops.",
    ),
    Question(
        id="py_006", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What is the difference between a shallow copy and a deep copy?",
        expected_keywords=["shallow", "deep", "copy", "reference", "nested", "independent", "module", "recursive"],
        model_answer_hint="Shallow copy creates a new object but references the same nested objects. Deep copy recursively creates new copies of all nested objects. Use copy.deepcopy() for deep copies.",
    ),
    Question(
        id="py_007", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What are Python decorators and why are they useful?",
        expected_keywords=["function", "wrapper", "modify", "behavior", "@", "higher-order", "reusable", "logging", "authentication"],
        model_answer_hint="Decorators are functions that modify the behavior of other functions. They wrap a function, adding functionality before/after it executes. Common uses: logging, authentication, timing, caching.",
    ),
    Question(
        id="py_008", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="Explain the concept of Python generators.",
        expected_keywords=["yield", "lazy", "memory", "iterator", "next", "one at a time", "efficient", "iterable"],
        model_answer_hint="Generators use 'yield' to produce values lazily, one at a time, without storing all values in memory. They implement the iterator protocol and are memory-efficient for large datasets.",
    ),
    Question(
        id="py_009", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What are the different data types in Python?",
        expected_keywords=["int", "float", "str", "bool", "list", "tuple", "dict", "set", "none", "dynamic typing"],
        model_answer_hint="Python has numeric types (int, float, complex), sequences (str, list, tuple), mappings (dict), sets (set, frozenset), boolean (bool), and NoneType. Python uses dynamic typing.",
    ),
    Question(
        id="py_010", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="How does exception handling work in Python?",
        expected_keywords=["try", "except", "finally", "raise", "exception", "error", "catch", "handle", "traceback"],
        model_answer_hint="Use try/except blocks to catch and handle exceptions. 'finally' runs cleanup code regardless. 'raise' throws exceptions. You can catch specific exception types or use a general except clause.",
    ),
    Question(
        id="py_011", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What is the difference between a module and a package in Python?",
        expected_keywords=["module", "package", "file", "directory", "__init__", "import", "namespace", "organization"],
        model_answer_hint="A module is a single .py file containing Python code. A package is a directory containing an __init__.py file and potentially multiple modules. Packages help organize code into namespaces.",
    ),
    Question(
        id="py_012", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What is the Global Interpreter Lock (GIL) in Python?",
        expected_keywords=["GIL", "thread", "mutex", "CPython", "one thread", "concurrency", "multiprocessing", "limitation"],
        model_answer_hint="The GIL is a mutex in CPython that allows only one thread to execute Python bytecode at a time. It simplifies memory management but limits true parallelism. Use multiprocessing for CPU-bound tasks.",
    ),
    Question(
        id="py_013", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="Explain the difference between append() and extend() for Python lists.",
        expected_keywords=["append", "extend", "single", "iterable", "element", "list", "add", "multiple"],
        model_answer_hint="append() adds a single element to the end of a list. extend() adds all elements from an iterable to the list. append([1,2]) adds one element (a list), extend([1,2]) adds two elements.",
    ),
    Question(
        id="py_014", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What is a virtual environment in Python and why use it?",
        expected_keywords=["isolated", "dependencies", "packages", "venv", "virtualenv", "project", "version", "conflict"],
        model_answer_hint="A virtual environment is an isolated Python environment for project-specific dependencies. It prevents version conflicts between projects. Created with 'python -m venv' or virtualenv.",
    ),
    Question(
        id="py_015", topic="python_basics", difficulty="easy", category="python",
        question_type="technical",
        text="What are Python's built-in string methods you use most often?",
        expected_keywords=["strip", "split", "join", "replace", "format", "lower", "upper", "find", "startswith", "endswith"],
        model_answer_hint="Common string methods: strip() removes whitespace, split() divides by delimiter, join() combines iterables, replace() substitutes text, format()/f-strings for interpolation, lower()/upper() for case.",
    ),
    # --- MEDIUM (20) ---
    Question(
        id="py_016", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain Python's method resolution order (MRO) in multiple inheritance.",
        expected_keywords=["MRO", "C3 linearization", "diamond problem", "super", "inheritance", "order", "mro()", "base class"],
        model_answer_hint="Python uses C3 linearization algorithm to determine method resolution order in multiple inheritance. It resolves the diamond problem by creating a consistent, predictable order. Use ClassName.mro() to inspect it.",
    ),
    Question(
        id="py_017", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="How do context managers work in Python? Explain the __enter__ and __exit__ methods.",
        expected_keywords=["with", "statement", "__enter__", "__exit__", "resource", "cleanup", "contextlib", "exception handling"],
        model_answer_hint="Context managers implement __enter__ (setup, return resource) and __exit__ (cleanup, handle exceptions) methods. Used with 'with' statement for automatic resource management. contextlib provides decorators for simpler creation.",
    ),
    Question(
        id="py_018", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain Python's descriptor protocol and its role in the language.",
        expected_keywords=["__get__", "__set__", "__delete__", "descriptor", "property", "class", "attribute", "data descriptor"],
        model_answer_hint="Descriptors define __get__, __set__, or __delete__ methods. They control attribute access on classes. Properties, classmethods, and staticmethods are all implemented using descriptors. Data descriptors (with __set__) take priority over instance __dict__.",
    ),
    Question(
        id="py_019", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="What are metaclasses in Python and when would you use them?",
        expected_keywords=["type", "class", "creation", "metaclass", "__new__", "__init__", "customize", "ORM", "framework"],
        model_answer_hint="Metaclasses are 'classes of classes' that control class creation. type is the default metaclass. Used in frameworks (Django ORM, SQLAlchemy) to customize class behavior. Override __new__ or __init__ on the metaclass.",
    ),
    Question(
        id="py_020", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain async/await in Python. How does asyncio work?",
        expected_keywords=["async", "await", "coroutine", "event loop", "non-blocking", "I/O", "concurrent", "asyncio", "gather"],
        model_answer_hint="async/await enables cooperative multitasking for I/O-bound tasks. Coroutines yield control at await points. The event loop manages scheduling. asyncio.gather() runs multiple coroutines concurrently. Best for network/file I/O, not CPU-bound work.",
    ),
    Question(
        id="py_021", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="How does Python's garbage collection work?",
        expected_keywords=["reference counting", "garbage collector", "cycle", "generational", "gc module", "memory", "del", "weak reference"],
        model_answer_hint="Python uses reference counting as the primary mechanism (objects deleted when count reaches 0) plus a generational garbage collector for detecting reference cycles. The gc module provides control over the cyclic collector.",
    ),
    Question(
        id="py_022", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain the difference between @staticmethod, @classmethod, and regular methods.",
        expected_keywords=["self", "cls", "instance", "class", "static", "no access", "factory", "inheritance"],
        model_answer_hint="Regular methods receive 'self' (instance). @classmethod receives 'cls' (class) and works with inheritance. @staticmethod receives no implicit argument, it's just a function in the class namespace. Use classmethod for factory patterns.",
    ),
    Question(
        id="py_023", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="What are dataclasses in Python and how do they compare to regular classes?",
        expected_keywords=["@dataclass", "auto", "__init__", "__repr__", "__eq__", "boilerplate", "type hints", "frozen", "field"],
        model_answer_hint="@dataclass auto-generates __init__, __repr__, __eq__ and other methods based on type-annotated fields. Reduces boilerplate for data-holding classes. Support frozen=True for immutability, field() for defaults.",
    ),
    Question(
        id="py_024", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="How would you implement a singleton pattern in Python?",
        expected_keywords=["singleton", "instance", "one", "__new__", "metaclass", "module", "decorator", "thread-safe"],
        model_answer_hint="Several approaches: override __new__ to control instance creation, use a metaclass, use a module-level instance (Python modules are singletons), or use a decorator. Consider thread-safety with locks.",
    ),
    Question(
        id="py_025", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain Python's memory model and variable scoping (LEGB rule).",
        expected_keywords=["LEGB", "local", "enclosing", "global", "built-in", "scope", "namespace", "nonlocal", "global keyword"],
        model_answer_hint="LEGB: Local → Enclosing → Global → Built-in scope resolution. Use 'global' keyword to modify global variables, 'nonlocal' for enclosing scope. Each function creates a new local scope.",
    ),
    Question(
        id="py_026", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="What is monkey patching in Python? When is it appropriate?",
        expected_keywords=["runtime", "modify", "dynamic", "testing", "mock", "patch", "attribute", "dangerous", "class"],
        model_answer_hint="Monkey patching is modifying classes or modules at runtime. Appropriate for testing (mocking), hot-fixing third-party code. Risky in production: breaks encapsulation, makes code harder to understand and maintain.",
    ),
    Question(
        id="py_027", topic="python_web", difficulty="medium", category="python",
        question_type="technical",
        text="Compare Django and Flask. When would you choose one over the other?",
        expected_keywords=["Django", "Flask", "batteries included", "lightweight", "ORM", "microframework", "admin", "scalability", "flexibility"],
        model_answer_hint="Django: full-featured (ORM, admin, auth built-in), opinionated, best for large apps. Flask: lightweight microframework, flexible, best for smaller apps or APIs. Django for rapid development with conventions, Flask for maximum control.",
    ),
    Question(
        id="py_028", topic="python_web", difficulty="medium", category="python",
        question_type="technical",
        text="How does FastAPI achieve better performance than Flask?",
        expected_keywords=["async", "ASGI", "uvicorn", "type hints", "pydantic", "validation", "starlette", "concurrent", "non-blocking"],
        model_answer_hint="FastAPI uses ASGI (async) instead of WSGI (sync), runs on uvicorn, leverages Python type hints for automatic validation via Pydantic, and builds on Starlette for high-performance async request handling.",
    ),
    Question(
        id="py_029", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain the iterator protocol in Python.",
        expected_keywords=["__iter__", "__next__", "StopIteration", "iterable", "iterator", "for loop", "protocol", "lazy"],
        model_answer_hint="The iterator protocol requires __iter__ (return self) and __next__ (return next value or raise StopIteration). Iterables have __iter__ that returns an iterator. For loops use this protocol internally.",
    ),
    Question(
        id="py_030", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="What are slots in Python classes and when should you use them?",
        expected_keywords=["__slots__", "memory", "dict", "attribute", "performance", "fixed", "instance", "optimization"],
        model_answer_hint="__slots__ declares fixed attributes, preventing __dict__ creation per instance. Saves memory (especially with many instances) and slightly faster attribute access. Trade-off: no dynamic attributes, complications with multiple inheritance.",
    ),
    Question(
        id="py_031", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="How do you handle concurrency in Python? Compare threading, multiprocessing, and asyncio.",
        expected_keywords=["threading", "multiprocessing", "asyncio", "GIL", "I/O-bound", "CPU-bound", "concurrent", "parallel", "event loop"],
        model_answer_hint="Threading: for I/O-bound tasks (limited by GIL for CPU). Multiprocessing: for CPU-bound tasks (separate processes, no GIL). Asyncio: for many I/O-bound tasks (single thread, cooperative scheduling). Choose based on workload type.",
    ),
    Question(
        id="py_032", topic="python_testing", difficulty="medium", category="python",
        question_type="technical",
        text="How do you write effective unit tests in Python with pytest?",
        expected_keywords=["pytest", "fixture", "assert", "mock", "parametrize", "test isolation", "coverage", "arrange-act-assert"],
        model_answer_hint="Use pytest with fixtures for setup/teardown, @parametrize for data-driven tests, mock/patch for dependencies. Follow AAA pattern (Arrange-Act-Assert). Aim for isolation and meaningful assertions. Use coverage to find gaps.",
    ),
    Question(
        id="py_033", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="Explain Python's type hinting system and tools like mypy.",
        expected_keywords=["type hints", "mypy", "typing", "annotation", "static analysis", "Optional", "Union", "Generic", "runtime"],
        model_answer_hint="Type hints (PEP 484) add optional static typing annotations. mypy performs static type checking. typing module provides Optional, Union, List, Dict, Generic types. Hints are not enforced at runtime but improve IDE support and catch bugs early.",
    ),
    Question(
        id="py_034", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="What design patterns do you commonly use in Python?",
        expected_keywords=["singleton", "factory", "observer", "strategy", "decorator", "adapter", "facade", "pattern", "SOLID"],
        model_answer_hint="Common Python patterns: Singleton (module-level), Factory (classmethod), Strategy (functions as first-class), Observer (callbacks/signals), Decorator (@ syntax). Python's dynamic nature makes some patterns simpler than in Java/C++.",
    ),
    Question(
        id="py_035", topic="python_advanced", difficulty="medium", category="python",
        question_type="technical",
        text="How do you profile and optimize Python code?",
        expected_keywords=["cProfile", "timeit", "memory_profiler", "bottleneck", "algorithm", "profiling", "optimization", "line_profiler"],
        model_answer_hint="Use cProfile for function-level profiling, line_profiler for line-by-line, memory_profiler for memory. timeit for micro-benchmarks. Optimize algorithms first, then data structures, then consider Cython/C extensions for hot paths.",
    ),
    # --- HARD (15) ---
    Question(
        id="py_036", topic="python_internals", difficulty="hard", category="python",
        question_type="technical",
        text="Explain CPython's object model and reference counting implementation.",
        expected_keywords=["PyObject", "ob_refcnt", "ob_type", "reference counting", "Py_INCREF", "Py_DECREF", "dealloc", "struct", "C level"],
        model_answer_hint="Every Python object is a PyObject struct with ob_refcnt (reference count) and ob_type (type pointer). Py_INCREF/Py_DECREF manage counts. When refcnt reaches 0, tp_dealloc frees memory. Additional cyclic GC handles reference cycles.",
    ),
    Question(
        id="py_037", topic="python_internals", difficulty="hard", category="python",
        question_type="technical",
        text="How does Python's import system work internally? Explain finders and loaders.",
        expected_keywords=["sys.meta_path", "finder", "loader", "module spec", "sys.modules", "cache", "importlib", "__path__", "namespace package"],
        model_answer_hint="Import system uses finders (sys.meta_path) to locate modules and loaders to execute them. sys.modules caches imports. importlib provides the machinery. Finders return ModuleSpec objects. Namespace packages allow split packages across directories.",
    ),
    Question(
        id="py_038", topic="python_internals", difficulty="hard", category="python",
        question_type="technical",
        text="How would you implement a custom Python memory allocator?",
        expected_keywords=["pymalloc", "arena", "pool", "block", "memory allocator", "ob_alloc", "PyMem", "small object", "256 bytes"],
        model_answer_hint="CPython's pymalloc uses a 3-tier system: arenas (256KB), pools (4KB, size-class specific), blocks (8-512 bytes). For custom allocation, override PyMem_SetAllocator or tp_alloc/tp_free. Small objects (<512B) use pymalloc, larger use system malloc.",
    ),
    Question(
        id="py_039", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="Explain how to implement a custom asynchronous context manager and async generator.",
        expected_keywords=["__aenter__", "__aexit__", "async with", "async for", "__aiter__", "__anext__", "asynccontextmanager", "yield"],
        model_answer_hint="Async context managers implement __aenter__ and __aexit__ as coroutines. Async generators use 'async def' with 'yield'. Use @asynccontextmanager decorator for simpler creation. Async for loops use __aiter__ and __anext__.",
    ),
    Question(
        id="py_040", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="Design a thread-safe connection pool in Python.",
        expected_keywords=["thread-safe", "lock", "semaphore", "queue", "pool", "connection", "context manager", "timeout", "reuse"],
        model_answer_hint="Use threading.Semaphore to limit pool size, Queue for available connections, Lock for state mutations. Implement as context manager for automatic release. Handle timeouts, connection validation, and lazy initialization.",
    ),
    Question(
        id="py_041", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="How would you implement a plugin system in Python?",
        expected_keywords=["entry_points", "importlib", "abstract", "interface", "register", "discover", "metaclass", "setuptools", "dynamic loading"],
        model_answer_hint="Options: setuptools entry_points for distributed plugins, importlib for dynamic loading, ABC for plugin interfaces, metaclass registration pattern, or directory scanning. Best practice: define abstract interface, auto-discover via entry_points or directory scan.",
    ),
    Question(
        id="py_042", topic="python_performance", difficulty="hard", category="python",
        question_type="technical",
        text="Explain how Python's dictionary implementation changed in Python 3.6+ and why.",
        expected_keywords=["compact", "ordered", "insertion order", "indices array", "entries array", "memory", "split table", "hash"],
        model_answer_hint="Python 3.6+ uses compact dictionaries: separate indices array (sparse) and entries array (dense, insertion-ordered). This saves ~25% memory over the old approach, maintains insertion order as a side effect, and improves cache locality.",
    ),
    Question(
        id="py_043", topic="python_performance", difficulty="hard", category="python",
        question_type="technical",
        text="How would you design a high-performance data processing pipeline in Python?",
        expected_keywords=["generator", "multiprocessing", "numpy", "vectorization", "batch", "memory-mapped", "Cython", "pool", "chunk"],
        model_answer_hint="Use generators for lazy streaming, multiprocessing.Pool for CPU parallelism, numpy for vectorized operations, memory-mapped files for large data, chunked processing to control memory. Consider Cython or C extensions for hot paths.",
    ),
    Question(
        id="py_044", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="How do you handle circular imports in Python? What are the root causes and solutions?",
        expected_keywords=["circular", "import", "deferred", "restructure", "TYPE_CHECKING", "local import", "dependency", "design"],
        model_answer_hint="Root cause: mutual module dependencies. Solutions: restructure to remove cycles, use deferred imports (import inside function), use TYPE_CHECKING for type-only imports, dependency injection, or create a shared interface module.",
    ),
    Question(
        id="py_045", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="Explain how to build a custom CPython extension module in C.",
        expected_keywords=["PyMethodDef", "PyModuleDef", "PyInit", "Py_BuildValue", "PyArg_ParseTuple", "extension", "C API", "reference counting"],
        model_answer_hint="Define PyMethodDef array for functions, PyModuleDef for module structure, PyInit_modulename as entry point. Use PyArg_ParseTuple to parse Python args, Py_BuildValue to return. Manage reference counting carefully with Py_INCREF/DECREF.",
    ),
    Question(
        id="py_046", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="How would you implement distributed task processing in Python?",
        expected_keywords=["Celery", "message queue", "Redis", "RabbitMQ", "worker", "task", "distributed", "retry", "idempotent"],
        model_answer_hint="Use Celery with Redis/RabbitMQ as message broker. Define idempotent tasks, configure workers with concurrency settings, implement retry logic with exponential backoff, use task chains/groups for workflows, monitor with Flower.",
    ),
    Question(
        id="py_047", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="Explain Python's abstract syntax tree (AST) and how to use it for code analysis.",
        expected_keywords=["ast", "parse", "NodeVisitor", "transform", "compile", "static analysis", "code generation", "tree"],
        model_answer_hint="ast.parse() converts source to AST nodes. NodeVisitor walks the tree for analysis, NodeTransformer modifies it. Use for linting, code metrics, transpilation. compile() converts AST back to code objects. Each node has type-specific fields.",
    ),
    Question(
        id="py_048", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="How do you ensure backward compatibility when evolving a Python API?",
        expected_keywords=["deprecation", "warnings", "semantic versioning", "adapter", "compatibility", "migration", "feature flags", "wrapper"],
        model_answer_hint="Use semantic versioning, emit DeprecationWarning before removal, provide migration guides, use adapter/wrapper patterns, feature flags for gradual rollout, maintain compatibility layers for at least one major version cycle.",
    ),
    Question(
        id="py_049", topic="python_security", difficulty="hard", category="python",
        question_type="technical",
        text="What are common security vulnerabilities in Python web applications and how do you prevent them?",
        expected_keywords=["injection", "XSS", "CSRF", "deserialization", "pickle", "eval", "input validation", "parameterized", "sanitize"],
        model_answer_hint="SQL injection (use parameterized queries), XSS (sanitize/escape output), CSRF (use tokens), unsafe deserialization (never unpickle untrusted data), eval/exec (never on user input), path traversal (validate paths), dependency vulnerabilities (audit packages).",
    ),
    Question(
        id="py_050", topic="python_advanced", difficulty="hard", category="python",
        question_type="technical",
        text="How would you implement a real-time event-driven system in Python?",
        expected_keywords=["asyncio", "websocket", "pub/sub", "event loop", "callback", "observer", "Redis", "channels", "reactive"],
        model_answer_hint="Use asyncio event loop as foundation, WebSocket for client communication, pub/sub (Redis) for distributed events, observer pattern for internal events. Consider frameworks like Django Channels or FastAPI WebSockets. Handle backpressure and connection management.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# JAVASCRIPT QUESTIONS (40)
# ═══════════════════════════════════════════════════════════════════════════════

JAVASCRIPT_QUESTIONS = [
    # --- EASY (12) ---
    Question(
        id="js_001", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What is the difference between var, let, and const in JavaScript?",
        expected_keywords=["scope", "hoisting", "block", "function", "reassignment", "const", "let", "var", "temporal dead zone"],
        model_answer_hint="var is function-scoped and hoisted. let is block-scoped, not hoisted to usable state. const is block-scoped and cannot be reassigned (but objects/arrays are still mutable). let and const have temporal dead zone.",
    ),
    Question(
        id="js_002", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="Explain closures in JavaScript.",
        expected_keywords=["closure", "scope", "outer", "function", "variable", "access", "lexical", "environment", "persist"],
        model_answer_hint="A closure is a function that retains access to its lexical scope's variables even after the outer function has returned. The inner function 'closes over' the variables, keeping them alive in memory.",
    ),
    Question(
        id="js_003", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What is the event loop in JavaScript? How does it handle asynchronous code?",
        expected_keywords=["event loop", "call stack", "callback queue", "microtask", "macrotask", "single-threaded", "non-blocking", "promise"],
        model_answer_hint="JavaScript is single-threaded. The event loop processes the call stack, then checks microtask queue (Promises), then macrotask queue (setTimeout). This enables non-blocking async code on a single thread.",
    ),
    Question(
        id="js_004", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What are Promises in JavaScript and how do they work?",
        expected_keywords=["Promise", "resolve", "reject", "then", "catch", "finally", "async", "pending", "fulfilled", "rejected"],
        model_answer_hint="Promises represent eventual completion/failure of async operations. States: pending → fulfilled/rejected. Chain with .then()/.catch()/.finally(). Avoid callback hell. Can use Promise.all(), Promise.race() for multiple promises.",
    ),
    Question(
        id="js_005", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="Explain the 'this' keyword in JavaScript.",
        expected_keywords=["this", "context", "binding", "call", "apply", "bind", "arrow function", "global", "object", "method"],
        model_answer_hint="'this' refers to the execution context. In methods: the object. In functions: global (or undefined in strict mode). Arrow functions inherit 'this' from enclosing scope. Use call/apply/bind to explicitly set 'this'.",
    ),
    Question(
        id="js_006", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What is the difference between == and === in JavaScript?",
        expected_keywords=["strict", "loose", "type coercion", "equality", "comparison", "type", "value", "===", "=="],
        model_answer_hint="== performs type coercion before comparison (loose equality). === checks both value AND type without coercion (strict equality). Always prefer === to avoid unexpected type conversion bugs.",
    ),
    Question(
        id="js_007", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="Explain destructuring in JavaScript with examples.",
        expected_keywords=["destructuring", "array", "object", "extract", "assignment", "default", "rest", "nested", "rename"],
        model_answer_hint="Destructuring extracts values from arrays/objects into variables. Array: [a, b] = [1, 2]. Object: {name, age} = person. Supports defaults, renaming (: alias), rest operator (...rest), and nested destructuring.",
    ),
    Question(
        id="js_008", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What are arrow functions and how do they differ from regular functions?",
        expected_keywords=["arrow", "=>", "this", "lexical", "concise", "no arguments", "no constructor", "implicit return"],
        model_answer_hint="Arrow functions (=>) have lexical 'this' binding (inherit from enclosing scope), no own 'arguments' object, cannot be used as constructors, have implicit return for single expressions. More concise syntax.",
    ),
    Question(
        id="js_009", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What is the spread operator and rest parameter in JavaScript?",
        expected_keywords=["spread", "rest", "...", "array", "object", "copy", "merge", "parameter", "expand"],
        model_answer_hint="Spread (...) expands iterables into elements: [...arr1, ...arr2] merges arrays, {...obj1, ...obj2} merges objects. Rest (...args) collects remaining arguments into an array in function parameters.",
    ),
    Question(
        id="js_010", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="Explain prototypal inheritance in JavaScript.",
        expected_keywords=["prototype", "__proto__", "chain", "inheritance", "Object.create", "constructor", "property lookup", "delegation"],
        model_answer_hint="JavaScript uses prototypal inheritance: objects inherit from other objects via the prototype chain. Property lookup traverses __proto__ links. Object.create() sets prototype directly. ES6 class syntax is sugar over prototypes.",
    ),
    Question(
        id="js_011", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What are template literals in JavaScript?",
        expected_keywords=["backtick", "interpolation", "${}", "multi-line", "tagged", "template", "string", "expression"],
        model_answer_hint="Template literals use backticks (`) for strings with embedded expressions via ${expression}, support multi-line strings without concatenation, and tagged templates for custom string processing.",
    ),
    Question(
        id="js_012", topic="js_basics", difficulty="easy", category="javascript",
        question_type="technical",
        text="What are higher-order functions in JavaScript? Give examples.",
        expected_keywords=["higher-order", "function", "argument", "return", "map", "filter", "reduce", "callback", "first-class"],
        model_answer_hint="Higher-order functions take functions as arguments or return functions. Examples: map(), filter(), reduce(), forEach(), sort(). They enable functional programming patterns. Functions are first-class citizens in JavaScript.",
    ),
    # --- MEDIUM (16) ---
    Question(
        id="js_013", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain the module system in JavaScript (CommonJS vs ES Modules).",
        expected_keywords=["CommonJS", "require", "module.exports", "ES modules", "import", "export", "static", "dynamic", "tree-shaking"],
        model_answer_hint="CommonJS: require/module.exports, synchronous, used in Node.js. ES Modules: import/export, static analysis enables tree-shaking, async loading. ES modules are the standard, CommonJS is legacy Node.js. ESM supports named and default exports.",
    ),
    Question(
        id="js_014", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="How does JavaScript handle memory management and garbage collection?",
        expected_keywords=["garbage collection", "mark-and-sweep", "reference", "memory leak", "closure", "circular", "heap", "reachability"],
        model_answer_hint="JavaScript uses mark-and-sweep GC: marks all reachable objects from roots, sweeps unmarked. Common leaks: forgotten timers, closures holding references, detached DOM nodes, global variables. V8 uses generational GC (young/old generation).",
    ),
    Question(
        id="js_015", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain the concept of currying in JavaScript.",
        expected_keywords=["currying", "partial", "function", "argument", "closure", "chain", "unary", "composition", "reusable"],
        model_answer_hint="Currying transforms a function with multiple arguments into a series of functions each taking one argument: f(a,b,c) → f(a)(b)(c). Uses closures to remember previous arguments. Enables partial application and function composition.",
    ),
    Question(
        id="js_016", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="What are generators in JavaScript and how do they work?",
        expected_keywords=["function*", "yield", "next", "iterator", "lazy", "pause", "resume", "done", "value"],
        model_answer_hint="Generators (function*) can pause execution at yield points and resume later. next() advances to next yield, returns {value, done}. Enable lazy evaluation, infinite sequences, and cooperative multitasking (with async generators).",
    ),
    Question(
        id="js_017", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain the Proxy and Reflect APIs in JavaScript.",
        expected_keywords=["Proxy", "Reflect", "handler", "trap", "get", "set", "intercept", "metaprogramming", "validation"],
        model_answer_hint="Proxy wraps an object with handler traps (get, set, has, deleteProperty, etc.) to intercept operations. Reflect provides default behavior for those operations. Use for validation, logging, reactive systems, and virtual objects.",
    ),
    Question(
        id="js_018", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="How do Web Workers enable multithreading in JavaScript?",
        expected_keywords=["Web Worker", "thread", "message", "postMessage", "parallel", "SharedArrayBuffer", "Atomics", "background", "CPU-intensive"],
        model_answer_hint="Web Workers run scripts in background threads. Communication via postMessage/onmessage (structured clone). SharedArrayBuffer for shared memory with Atomics for synchronization. Good for CPU-intensive tasks without blocking the main thread.",
    ),
    Question(
        id="js_019", topic="js_performance", difficulty="medium", category="javascript",
        question_type="technical",
        text="What are common JavaScript performance optimization techniques?",
        expected_keywords=["debounce", "throttle", "lazy loading", "virtual DOM", "memoization", "bundle", "code splitting", "cache", "requestAnimationFrame"],
        model_answer_hint="Debounce/throttle for event handlers, lazy loading for resources, memoization for expensive calculations, code splitting for smaller bundles, requestAnimationFrame for animations, virtual scrolling for large lists, efficient DOM manipulation.",
    ),
    Question(
        id="js_020", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain WeakMap and WeakSet. When would you use them?",
        expected_keywords=["WeakMap", "WeakSet", "garbage collection", "weak reference", "memory leak", "private", "metadata", "cache"],
        model_answer_hint="WeakMap/WeakSet hold weak references to keys—if no other reference exists, the entry is garbage collected. Use for: private data storage, caching metadata about objects without preventing GC, tracking DOM elements.",
    ),
    Question(
        id="js_021", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="How does async/await work under the hood in JavaScript?",
        expected_keywords=["async", "await", "Promise", "generator", "state machine", "microtask", "suspend", "resume", "transpile"],
        model_answer_hint="async/await is syntactic sugar over Promises. Under the hood, async functions are compiled to state machines (like generators). await suspends execution, schedules continuation as a microtask when the Promise resolves. The engine transforms it into chained .then() calls.",
    ),
    Question(
        id="js_022", topic="typescript", difficulty="medium", category="javascript",
        question_type="technical",
        text="What are the benefits of TypeScript over plain JavaScript?",
        expected_keywords=["type safety", "static analysis", "IDE", "refactoring", "interfaces", "generics", "compile-time", "documentation", "maintainability"],
        model_answer_hint="TypeScript adds: static type checking catches bugs early, better IDE support (autocomplete, refactoring), interfaces/generics for better abstractions, serves as documentation, easier large-scale refactoring, gradual adoption possible.",
    ),
    Question(
        id="js_023", topic="typescript", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain TypeScript generics and utility types.",
        expected_keywords=["generic", "T", "constraint", "Partial", "Required", "Pick", "Omit", "Record", "type parameter", "reusable"],
        model_answer_hint="Generics use type parameters (T) for reusable typed code. Constraints (extends) limit types. Utility types: Partial<T> (all optional), Required<T>, Pick<T, K>, Omit<T, K>, Record<K, V>. Enable type-safe generic containers and functions.",
    ),
    Question(
        id="js_024", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="What is the difference between Object.freeze(), Object.seal(), and Object.preventExtensions()?",
        expected_keywords=["freeze", "seal", "preventExtensions", "immutable", "property", "add", "delete", "modify", "writable"],
        model_answer_hint="preventExtensions: can't add properties. seal: can't add/delete, but can modify existing. freeze: fully immutable (no add/delete/modify). All are shallow—nested objects need recursive application (deep freeze).",
    ),
    Question(
        id="js_025", topic="js_patterns", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain the Observer pattern in JavaScript and how it relates to EventEmitter.",
        expected_keywords=["observer", "subscribe", "publish", "emit", "listener", "event", "decouple", "EventEmitter", "callback"],
        model_answer_hint="Observer pattern: subjects notify observers of state changes. In JS: EventEmitter (Node.js) or EventTarget (browser). subscribe/on to add listeners, emit/dispatchEvent to notify. Decouples producers from consumers.",
    ),
    Question(
        id="js_026", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="How do you handle errors in async JavaScript code?",
        expected_keywords=["try-catch", "await", "catch", "unhandledRejection", "error boundary", "global handler", "async", "Promise.allSettled"],
        model_answer_hint="Use try/catch around await calls, .catch() on Promises, process.on('unhandledRejection') for global handling. Promise.allSettled() for handling multiple async operations. Error boundaries in React. Always provide meaningful error messages.",
    ),
    Question(
        id="js_027", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="What is event delegation and why is it important?",
        expected_keywords=["delegation", "bubbling", "parent", "event", "listener", "performance", "dynamic", "target", "efficient"],
        model_answer_hint="Event delegation attaches a single listener to a parent element instead of each child. Uses event bubbling—check event.target to identify the source. Benefits: fewer listeners (better performance), works with dynamically added elements.",
    ),
    Question(
        id="js_028", topic="js_advanced", difficulty="medium", category="javascript",
        question_type="technical",
        text="Explain the concept of immutability in JavaScript and libraries that help achieve it.",
        expected_keywords=["immutable", "spread", "Object.freeze", "immer", "persistent", "structural sharing", "pure function", "predictable"],
        model_answer_hint="Immutability means data is never modified, only replaced with new copies. Techniques: spread operator, Object.freeze (shallow), libraries like Immer (structural sharing, produce()). Benefits: predictable state, easier debugging, time-travel debugging.",
    ),
    # --- HARD (12) ---
    Question(
        id="js_029", topic="js_internals", difficulty="hard", category="javascript",
        question_type="technical",
        text="Explain V8's hidden classes and inline caching optimization.",
        expected_keywords=["hidden class", "inline cache", "shape", "transition", "monomorphic", "polymorphic", "deoptimization", "V8", "optimization"],
        model_answer_hint="V8 creates hidden classes (shapes/maps) for objects with same structure. Inline caches store property access paths for fast lookups. Monomorphic (one shape) is fastest. Adding properties in different orders creates different hidden classes, defeating optimization.",
    ),
    Question(
        id="js_030", topic="js_internals", difficulty="hard", category="javascript",
        question_type="technical",
        text="How does V8's JIT compilation pipeline work (Ignition → TurboFan)?",
        expected_keywords=["Ignition", "TurboFan", "bytecode", "JIT", "optimization", "deoptimization", "hot function", "type feedback", "interpreter"],
        model_answer_hint="Ignition: interprets bytecode, collects type feedback. TurboFan: optimizing JIT compiler for hot functions using type feedback. Speculative optimizations based on observed types. Deoptimizes to bytecode if assumptions are violated (type mismatch).",
    ),
    Question(
        id="js_031", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="Design a reactive state management system from scratch.",
        expected_keywords=["observable", "subscriber", "dependency", "tracking", "proxy", "computed", "effect", "notify", "reactive"],
        model_answer_hint="Use Proxy for reactive objects that track dependencies. When a value is read in an effect, record the dependency. On mutation, notify all dependent effects. Implement computed values as cached effects. Batch updates for performance (microtask scheduling).",
    ),
    Question(
        id="js_032", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="How would you implement a custom bundler that handles ES module resolution?",
        expected_keywords=["AST", "dependency graph", "resolve", "transform", "bundle", "tree-shaking", "circular", "scope hoisting", "chunks"],
        model_answer_hint="Parse files to AST, resolve import paths (follow node_modules algorithm), build dependency graph, detect circular dependencies, perform tree-shaking (remove unused exports via AST), concatenate/scope-hoist modules, emit chunks with proper module wrapping.",
    ),
    Question(
        id="js_033", topic="js_performance", difficulty="hard", category="javascript",
        question_type="technical",
        text="Explain techniques for achieving sub-second page loads in a complex JavaScript application.",
        expected_keywords=["code splitting", "SSR", "preload", "critical CSS", "lazy loading", "service worker", "CDN", "compression", "tree-shaking", "edge rendering"],
        model_answer_hint="Critical rendering path optimization: SSR/streaming for first paint, code splitting/lazy loading for non-critical JS, preload critical resources, aggressive caching with service workers, CDN at edge, compression (brotli), tree-shaking, image optimization, HTTP/2.",
    ),
    Question(
        id="js_034", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="How would you implement a JavaScript virtual machine or interpreter?",
        expected_keywords=["tokenizer", "parser", "AST", "interpreter", "scope chain", "environment", "stack", "bytecode", "evaluate"],
        model_answer_hint="Steps: tokenizer (lexer) → parser (produce AST) → interpreter (tree-walking or compile to bytecode). Implement scope chain via Environment objects. Handle closures by capturing environments. Stack for execution contexts. Support prototype-based objects.",
    ),
    Question(
        id="js_035", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="Explain the Temporal API and how it improves upon Date.",
        expected_keywords=["Temporal", "immutable", "timezone", "calendar", "duration", "instant", "ZonedDateTime", "PlainDate", "unambiguous"],
        model_answer_hint="Temporal provides immutable date/time types (PlainDate, PlainTime, ZonedDateTime, Instant, Duration), proper timezone support, calendar-aware operations, no ambiguous parsing, arithmetic without mutation, and clear separation of concepts (wall-clock vs. absolute time).",
    ),
    Question(
        id="js_036", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="How do you design a fault-tolerant real-time WebSocket system?",
        expected_keywords=["WebSocket", "reconnect", "heartbeat", "exponential backoff", "message queue", "acknowledgment", "buffering", "fallback", "state sync"],
        model_answer_hint="Implement: automatic reconnection with exponential backoff, heartbeat/ping-pong for connection health, client-side message buffering during disconnects, server acknowledgments with retry, state synchronization on reconnect, graceful fallback to long-polling.",
    ),
    Question(
        id="js_037", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="Explain how to implement structural sharing for an immutable data structure library.",
        expected_keywords=["structural sharing", "trie", "HAMT", "persistent", "path copying", "node reuse", "memory efficient", "immutable"],
        model_answer_hint="Use Hash Array Mapped Tries (HAMT): tree structure where updates create new path from root to changed leaf, sharing all unmodified subtrees. Path copying ensures O(log32 N) updates while reusing most memory. Immer and Immutable.js use variants of this.",
    ),
    Question(
        id="js_038", topic="js_security", difficulty="hard", category="javascript",
        question_type="technical",
        text="What are the security implications of eval(), innerHTML, and dynamic script injection?",
        expected_keywords=["XSS", "eval", "innerHTML", "Content-Security-Policy", "sanitize", "injection", "CSP", "trusted types", "DOM-based"],
        model_answer_hint="eval() executes arbitrary code (code injection). innerHTML parses HTML (XSS via script injection). Dynamic script loading can load malicious code. Mitigations: Content-Security-Policy headers, Trusted Types API, DOMPurify for sanitization, textContent instead of innerHTML.",
    ),
    Question(
        id="js_039", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="How would you implement a custom React-like virtual DOM diffing algorithm?",
        expected_keywords=["virtual DOM", "diff", "reconciliation", "patch", "key", "fiber", "tree", "minimal updates", "heuristic"],
        model_answer_hint="Create virtual DOM tree (plain objects), diff old vs new tree: same type → update props, different type → replace, list → use keys for O(n) reconciliation. Generate minimal patch operations. Apply patches to real DOM. Use heuristics (same level comparison, keys) to avoid O(n³) complexity.",
    ),
    Question(
        id="js_040", topic="js_advanced", difficulty="hard", category="javascript",
        question_type="technical",
        text="Explain how to build a compile-time optimization plugin for a JavaScript bundler.",
        expected_keywords=["AST", "transform", "plugin", "visitor pattern", "babel", "dead code", "constant folding", "compile-time", "static analysis"],
        model_answer_hint="Write a Babel/esbuild plugin using visitor pattern on AST nodes. Implement transforms: constant folding (evaluate static expressions), dead code elimination (remove unreachable branches), inline small functions, replace env variables. Test with snapshot tests of transformed output.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# REACT QUESTIONS (35)
# ═══════════════════════════════════════════════════════════════════════════════

REACT_QUESTIONS = [
    # --- EASY (10) ---
    Question(
        id="react_001", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What is the Virtual DOM and how does React use it?",
        expected_keywords=["virtual DOM", "reconciliation", "diff", "performance", "real DOM", "batch", "update", "render", "tree"],
        model_answer_hint="Virtual DOM is an in-memory representation of the real DOM. React diffs the new virtual DOM against the previous one, calculates minimal changes, and batches updates to the real DOM. This avoids expensive direct DOM manipulation.",
    ),
    Question(
        id="react_002", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="Explain the difference between state and props in React.",
        expected_keywords=["state", "props", "internal", "external", "mutable", "immutable", "parent", "child", "re-render", "own"],
        model_answer_hint="Props are passed from parent to child (read-only to the child). State is managed internally by a component (mutable via setState/useState). Changes to either trigger re-renders. Props flow down, state is local.",
    ),
    Question(
        id="react_003", topic="react_hooks", difficulty="easy", category="react",
        question_type="technical",
        text="Explain the useState and useEffect hooks.",
        expected_keywords=["useState", "useEffect", "state", "side effect", "cleanup", "dependency", "re-render", "lifecycle", "array"],
        model_answer_hint="useState returns [value, setter] for component state. useEffect runs side effects after render—takes a callback and dependency array. Empty deps = mount only. Return function for cleanup (unmount/re-run). Replaces componentDidMount/Update/Unmount.",
    ),
    Question(
        id="react_004", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What is JSX and how does it work?",
        expected_keywords=["JSX", "syntax", "React.createElement", "transform", "Babel", "HTML-like", "expression", "compile", "JavaScript"],
        model_answer_hint="JSX is a syntax extension that allows HTML-like code in JavaScript. Babel transforms JSX into React.createElement() calls. It's syntactic sugar, not HTML—supports JS expressions in {}, has different attribute names (className, htmlFor).",
    ),
    Question(
        id="react_005", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What are React keys and why are they important?",
        expected_keywords=["key", "unique", "list", "reconciliation", "identity", "performance", "index", "reorder", "stable"],
        model_answer_hint="Keys help React identify which list items have changed, been added, or removed. They should be unique and stable (not array index). Proper keys enable efficient reconciliation by preserving component state during reorders.",
    ),
    Question(
        id="react_006", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What is the difference between controlled and uncontrolled components?",
        expected_keywords=["controlled", "uncontrolled", "state", "ref", "form", "value", "onChange", "DOM", "source of truth"],
        model_answer_hint="Controlled components: form data managed by React state (value + onChange). Uncontrolled components: form data managed by DOM itself (use refs to read values). Controlled gives more control but requires more code.",
    ),
    Question(
        id="react_007", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="How do you handle events in React?",
        expected_keywords=["synthetic event", "camelCase", "handler", "function", "bind", "preventDefault", "onClick", "event pooling"],
        model_answer_hint="React uses SyntheticEvents (cross-browser wrapper). Events are camelCase (onClick, onChange). Pass function references, don't call them. Use preventDefault() to prevent defaults. Arrow functions or bind for 'this' in class components.",
    ),
    Question(
        id="react_008", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What is conditional rendering in React?",
        expected_keywords=["conditional", "ternary", "&&", "if", "render", "null", "component", "short-circuit", "display"],
        model_answer_hint="Render different UI based on conditions using: ternary operator (condition ? A : B), logical && (condition && <Component/>), if/else in render logic, or early return with null. Choose based on readability.",
    ),
    Question(
        id="react_009", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="What are React fragments and when should you use them?",
        expected_keywords=["Fragment", "<>", "wrapper", "DOM", "extra node", "group", "list", "key", "children"],
        model_answer_hint="Fragments (<Fragment> or <>) group multiple children without adding extra DOM nodes. Use when a component must return multiple elements. Keyed fragments (<Fragment key={}>) for lists. Avoids unnecessary wrapper divs.",
    ),
    Question(
        id="react_010", topic="react_basics", difficulty="easy", category="react",
        question_type="technical",
        text="How does component composition work in React?",
        expected_keywords=["composition", "children", "props", "reusable", "nesting", "slot", "container", "presentational", "higher-order"],
        model_answer_hint="Composition: build complex UIs from simple, reusable components. Use children prop for content injection, render props for behavior sharing, container/presentational pattern for logic separation. Prefer composition over inheritance.",
    ),
    # --- MEDIUM (15) ---
    Question(
        id="react_011", topic="react_hooks", difficulty="medium", category="react",
        question_type="technical",
        text="Explain useCallback and useMemo. When should you use them?",
        expected_keywords=["useCallback", "useMemo", "memoize", "reference", "performance", "re-render", "dependency", "expensive", "stable"],
        model_answer_hint="useMemo memoizes computed values (avoids expensive recalculations). useCallback memoizes function references (avoids child re-renders from new function references). Use when passing callbacks to memoized children or in expensive computations. Don't overuse—they have overhead.",
    ),
    Question(
        id="react_012", topic="react_hooks", difficulty="medium", category="react",
        question_type="technical",
        text="How does useContext work and when should you use it vs. Redux?",
        expected_keywords=["useContext", "Context", "Provider", "Consumer", "global state", "prop drilling", "Redux", "re-render", "lightweight"],
        model_answer_hint="useContext accesses Context values without prop drilling. Context triggers re-renders for all consumers on change. Redux for complex state with actions/reducers/middleware. Context for simpler global state (theme, auth). Redux has better performance for frequent updates.",
    ),
    Question(
        id="react_013", topic="react_hooks", difficulty="medium", category="react",
        question_type="technical",
        text="Explain useReducer and when to prefer it over useState.",
        expected_keywords=["useReducer", "dispatch", "action", "reducer", "complex state", "next state", "predictable", "testing", "state machine"],
        model_answer_hint="useReducer manages complex state with reducer function (state, action) → newState. Prefer over useState when: state logic is complex, multiple sub-values, next state depends on previous, or state transitions need to be testable/predictable.",
    ),
    Question(
        id="react_014", topic="react_performance", difficulty="medium", category="react",
        question_type="technical",
        text="How do you optimize React application performance?",
        expected_keywords=["memo", "useMemo", "useCallback", "lazy", "Suspense", "virtualization", "code splitting", "profiler", "shouldComponentUpdate"],
        model_answer_hint="React.memo for component memoization, useMemo/useCallback for values/functions, React.lazy + Suspense for code splitting, virtualization for long lists, avoid unnecessary state lifts, proper key usage, React Profiler to identify bottlenecks.",
    ),
    Question(
        id="react_015", topic="react_patterns", difficulty="medium", category="react",
        question_type="technical",
        text="Explain the render props pattern and custom hooks as alternatives.",
        expected_keywords=["render props", "custom hook", "reuse", "logic", "sharing", "composition", "function as child", "abstraction"],
        model_answer_hint="Render props: pass a function as prop that returns JSX (shares logic via function argument). Custom hooks: extract reusable stateful logic into functions (use* naming). Custom hooks are now preferred—cleaner syntax, better composability, no nesting hell.",
    ),
    Question(
        id="react_016", topic="react_state", difficulty="medium", category="react",
        question_type="technical",
        text="Compare Redux, Zustand, and React Query for state management.",
        expected_keywords=["Redux", "Zustand", "React Query", "server state", "client state", "boilerplate", "devtools", "cache", "middleware"],
        model_answer_hint="Redux: powerful but verbose, best for complex client state. Zustand: simpler API, less boilerplate, good for medium apps. React Query: specifically for server state (caching, sync, invalidation). Use React Query for API data + Zustand/Redux for client-only state.",
    ),
    Question(
        id="react_017", topic="react_patterns", difficulty="medium", category="react",
        question_type="technical",
        text="How do you handle forms in React? Compare different approaches.",
        expected_keywords=["controlled", "uncontrolled", "Formik", "React Hook Form", "validation", "state", "ref", "performance", "submission"],
        model_answer_hint="Controlled (state per field) for simple forms. React Hook Form: uncontrolled with refs, minimal re-renders, great performance. Formik: controlled, more features but more re-renders. React Hook Form preferred for complex forms. Add validation with Yup/Zod.",
    ),
    Question(
        id="react_018", topic="react_advanced", difficulty="medium", category="react",
        question_type="technical",
        text="What are error boundaries and how do you implement them?",
        expected_keywords=["error boundary", "componentDidCatch", "getDerivedStateFromError", "fallback", "class component", "catch", "tree", "production"],
        model_answer_hint="Error boundaries are class components with getDerivedStateFromError (render fallback) and componentDidCatch (log error). They catch errors in child component tree during render. Don't catch: event handlers, async code, SSR, own errors. No hook equivalent yet.",
    ),
    Question(
        id="react_019", topic="react_advanced", difficulty="medium", category="react",
        question_type="technical",
        text="Explain React's Suspense and its use cases.",
        expected_keywords=["Suspense", "fallback", "lazy", "loading", "concurrent", "data fetching", "streaming", "boundary", "waterfall"],
        model_answer_hint="Suspense shows fallback UI while children are loading. Use with React.lazy for code splitting, data fetching (React 18+), and streaming SSR. Eliminates loading state boilerplate. Multiple Suspense boundaries for granular loading states.",
    ),
    Question(
        id="react_020", topic="react_testing", difficulty="medium", category="react",
        question_type="technical",
        text="How do you test React components effectively?",
        expected_keywords=["React Testing Library", "render", "screen", "userEvent", "jest", "mock", "integration", "accessibility", "query"],
        model_answer_hint="Use React Testing Library: test behavior not implementation. render() component, query by accessible roles/text (screen.getByRole), simulate interactions with userEvent, assert expected outcomes. Mock API calls. Prefer integration tests over unit tests for components.",
    ),
    Question(
        id="react_021", topic="react_advanced", difficulty="medium", category="react",
        question_type="technical",
        text="What is server-side rendering (SSR) in React and how does Next.js implement it?",
        expected_keywords=["SSR", "hydration", "SEO", "getServerSideProps", "getStaticProps", "Next.js", "initial load", "server", "pre-render"],
        model_answer_hint="SSR renders React on the server, sends HTML to client, then hydrates (attach event handlers). Next.js provides getServerSideProps (per-request SSR), getStaticProps (build-time), and ISR. Benefits: SEO, faster initial load, social media previews.",
    ),
    Question(
        id="react_022", topic="react_hooks", difficulty="medium", category="react",
        question_type="technical",
        text="Explain useRef and its use cases beyond DOM access.",
        expected_keywords=["useRef", "ref", "mutable", "persist", "render", "DOM", "current", "previous value", "timer", "no re-render"],
        model_answer_hint="useRef creates a mutable .current container that persists across renders without causing re-renders. Uses: DOM element access, storing previous values, timer IDs, any mutable value that shouldn't trigger re-render. Like an instance variable.",
    ),
    Question(
        id="react_023", topic="react_patterns", difficulty="medium", category="react",
        question_type="technical",
        text="How do you implement code splitting in a React application?",
        expected_keywords=["React.lazy", "Suspense", "dynamic import", "code splitting", "bundle", "route-based", "component-based", "webpack", "loading"],
        model_answer_hint="Use React.lazy(() => import('./Component')) with Suspense wrapper for component-level splitting. Route-based splitting is most impactful. Dynamic imports for heavy libraries. Webpack/Vite automatically creates chunks. Prefetch for predicted navigation.",
    ),
    Question(
        id="react_024", topic="react_advanced", difficulty="medium", category="react",
        question_type="technical",
        text="What are React portals and when would you use them?",
        expected_keywords=["portal", "createPortal", "DOM", "modal", "tooltip", "overflow", "z-index", "event bubbling", "outside"],
        model_answer_hint="Portals render children into a different DOM node outside the parent hierarchy. Use for modals, tooltips, dropdowns that need to escape overflow:hidden or z-index stacking contexts. Events still bubble through the React tree, not the DOM tree.",
    ),
    Question(
        id="react_025", topic="react_state", difficulty="medium", category="react",
        question_type="technical",
        text="How do you handle global state without Redux?",
        expected_keywords=["Context", "useReducer", "Zustand", "Jotai", "Recoil", "atom", "store", "provider", "prop drilling"],
        model_answer_hint="Options: Context + useReducer for simple global state, Zustand for minimal boilerplate stores, Jotai/Recoil for atomic state, React Query for server state. Context re-render issue can be solved with selector patterns or state splitting.",
    ),
    # --- HARD (10) ---
    Question(
        id="react_026", topic="react_internals", difficulty="hard", category="react",
        question_type="technical",
        text="Explain React's Fiber architecture and reconciliation algorithm.",
        expected_keywords=["Fiber", "reconciliation", "work loop", "priority", "interruptible", "unit of work", "tree", "commit phase", "render phase"],
        model_answer_hint="Fiber is a reimplementation of React's core algorithm. Each component is a Fiber node (unit of work). Work is interruptible—high-priority updates (user input) can interrupt low-priority (data fetch). Two phases: render (build Fiber tree, interruptible) and commit (apply changes, synchronous).",
    ),
    Question(
        id="react_027", topic="react_internals", difficulty="hard", category="react",
        question_type="technical",
        text="How does React 18's concurrent rendering work?",
        expected_keywords=["concurrent", "startTransition", "useTransition", "useDeferredValue", "priority", "interrupt", "streaming", "automatic batching"],
        model_answer_hint="Concurrent rendering allows React to interrupt and prioritize work. startTransition marks low-priority updates. useTransition provides pending state. useDeferredValue defers expensive re-renders. Automatic batching groups state updates. Streaming SSR with selective hydration.",
    ),
    Question(
        id="react_028", topic="react_advanced", difficulty="hard", category="react",
        question_type="technical",
        text="How would you build a design system component library with React?",
        expected_keywords=["design tokens", "composability", "accessibility", "polymorphic", "variant", "theming", "documentation", "testing", "tree-shaking"],
        model_answer_hint="Design tokens for consistent values, polymorphic 'as' prop for flexible rendering, variant/size props via cva/class-variance-authority, compound components for composition, full a11y (ARIA), Storybook for docs, comprehensive testing, tree-shakeable exports.",
    ),
    Question(
        id="react_029", topic="react_performance", difficulty="hard", category="react",
        question_type="technical",
        text="How do you debug and fix React performance issues at scale?",
        expected_keywords=["Profiler", "why-did-you-render", "memo", "virtualization", "bundle analysis", "re-render", "flame chart", "commit", "bottleneck"],
        model_answer_hint="React DevTools Profiler to identify slow commits, why-did-you-render to catch unnecessary re-renders, bundle analyzer for code size, virtualize long lists (react-window), optimize with memo/useMemo/useCallback strategically, split contexts, lazy load routes.",
    ),
    Question(
        id="react_030", topic="react_architecture", difficulty="hard", category="react",
        question_type="technical",
        text="How do you architect a large-scale React application?",
        expected_keywords=["feature-based", "module", "lazy loading", "state management", "testing strategy", "monorepo", "design system", "separation of concerns"],
        model_answer_hint="Feature-based folder structure, lazy-loaded route modules, layered state (server state + client state + UI state), shared design system package, monorepo with Turborepo/Nx, comprehensive testing pyramid, clear API contracts, code ownership per module.",
    ),
    Question(
        id="react_031", topic="react_advanced", difficulty="hard", category="react",
        question_type="technical",
        text="Explain React Server Components and how they change the architecture.",
        expected_keywords=["Server Components", "client components", "bundle size", "streaming", "zero-bundle", "async", "use client", "RSC payload"],
        model_answer_hint="Server Components render on server with zero client JS bundle. They can access databases/files directly, stream to client. Client Components ('use client') handle interactivity. RSC payload is a special serialization format. Reduces bundle size significantly. Eliminates need for many API endpoints.",
    ),
    Question(
        id="react_032", topic="react_advanced", difficulty="hard", category="react",
        question_type="technical",
        text="How would you implement an accessible, compound component pattern?",
        expected_keywords=["compound", "Context", "children", "implicit state", "accessible", "ARIA", "keyboard", "roving tabindex", "composable"],
        model_answer_hint="Compound components share implicit state via Context. Parent manages state, children consume via useContext. Implement roving tabindex for keyboard navigation, ARIA roles/attributes, proper focus management. Example: Tabs (TabList + Tab + TabPanel) sharing active index.",
    ),
    Question(
        id="react_033", topic="react_advanced", difficulty="hard", category="react",
        question_type="technical",
        text="How do you implement optimistic updates with proper rollback?",
        expected_keywords=["optimistic", "rollback", "cache", "mutation", "error", "revert", "snapshot", "invalidate", "React Query"],
        model_answer_hint="Update UI immediately before server confirms. Save previous state snapshot. On success: invalidate/refetch. On error: rollback to snapshot, show error notification. React Query's useMutation supports onMutate (optimistic), onError (rollback), onSettled (invalidate).",
    ),
    Question(
        id="react_034", topic="react_performance", difficulty="hard", category="react",
        question_type="technical",
        text="How do you handle real-time data in React with WebSockets at scale?",
        expected_keywords=["WebSocket", "reconnection", "throttle", "batch updates", "subscription", "stale data", "normalization", "memory", "unsubscribe"],
        model_answer_hint="Custom hook for WebSocket lifecycle (connect, reconnect, cleanup). Throttle/batch incoming updates to reduce re-renders. Normalize data for efficient updates. Handle reconnection with exponential backoff. Unsubscribe on unmount. Consider server-sent events for simpler one-way streams.",
    ),
    Question(
        id="react_035", topic="react_advanced", difficulty="hard", category="react",
        question_type="technical",
        text="Explain micro-frontend architecture with React and Module Federation.",
        expected_keywords=["micro-frontend", "Module Federation", "webpack", "shared", "runtime", "independent", "deploy", "remote", "host"],
        model_answer_hint="Micro-frontends split app into independently deployable React apps. Webpack Module Federation loads remote modules at runtime. Shared dependencies (React) loaded once. Each team owns a remote, host shell composes them. Challenges: shared state, routing, consistent UX.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SQL QUESTIONS (40)
# ═══════════════════════════════════════════════════════════════════════════════

SQL_QUESTIONS = [
    # --- EASY (12) ---
    Question(
        id="sql_001", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is the difference between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN?",
        expected_keywords=["INNER", "LEFT", "RIGHT", "FULL", "matching", "null", "all rows", "intersection", "outer"],
        model_answer_hint="INNER: only matching rows from both tables. LEFT: all from left + matching right (NULL if no match). RIGHT: all from right + matching left. FULL OUTER: all from both (NULL where no match). Think set operations.",
    ),
    Question(
        id="sql_002", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is normalization and what are the normal forms?",
        expected_keywords=["1NF", "2NF", "3NF", "BCNF", "redundancy", "dependency", "atomic", "decomposition", "anomaly"],
        model_answer_hint="Normalization reduces redundancy. 1NF: atomic values, no repeating groups. 2NF: 1NF + no partial dependencies. 3NF: 2NF + no transitive dependencies. BCNF: every determinant is a candidate key. Higher NFs trade write performance for data integrity.",
    ),
    Question(
        id="sql_003", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is the difference between WHERE and HAVING clauses?",
        expected_keywords=["WHERE", "HAVING", "filter", "aggregate", "GROUP BY", "before", "after", "condition", "rows"],
        model_answer_hint="WHERE filters individual rows before grouping. HAVING filters groups after GROUP BY and aggregation. WHERE can't use aggregate functions (COUNT, SUM, etc.), HAVING can. WHERE is processed first in execution order.",
    ),
    Question(
        id="sql_004", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="Explain the difference between DELETE, TRUNCATE, and DROP.",
        expected_keywords=["DELETE", "TRUNCATE", "DROP", "rows", "table", "rollback", "WHERE", "structure", "log"],
        model_answer_hint="DELETE: removes rows (can use WHERE, logged, rollbackable). TRUNCATE: removes all rows (faster, minimal logging, resets identity). DROP: removes entire table structure and data permanently. DELETE triggers fire, TRUNCATE doesn't.",
    ),
    Question(
        id="sql_005", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What are indexes in SQL and why are they important?",
        expected_keywords=["index", "B-tree", "performance", "lookup", "search", "trade-off", "write", "read", "clustered", "non-clustered"],
        model_answer_hint="Indexes are data structures (typically B-tree) that speed up data retrieval. Clustered index defines physical row order (one per table). Non-clustered has separate structure pointing to rows. Trade-off: faster reads, slower writes (maintenance overhead).",
    ),
    Question(
        id="sql_006", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What are aggregate functions in SQL? Give examples.",
        expected_keywords=["COUNT", "SUM", "AVG", "MIN", "MAX", "aggregate", "GROUP BY", "NULL", "function"],
        model_answer_hint="Aggregate functions perform calculations on sets of rows: COUNT (number of rows), SUM (total), AVG (average), MIN/MAX (smallest/largest). Used with GROUP BY. Most ignore NULLs (except COUNT(*)).",
    ),
    Question(
        id="sql_007", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is a primary key and a foreign key?",
        expected_keywords=["primary key", "foreign key", "unique", "not null", "reference", "relationship", "constraint", "integrity", "parent"],
        model_answer_hint="Primary key: uniquely identifies each row (unique + not null). Foreign key: references a primary key in another table, establishing a relationship. Foreign keys enforce referential integrity—child records must reference existing parent records.",
    ),
    Question(
        id="sql_008", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is the difference between UNION and UNION ALL?",
        expected_keywords=["UNION", "UNION ALL", "duplicate", "distinct", "combine", "performance", "set", "rows", "remove"],
        model_answer_hint="UNION combines results and removes duplicates (performs DISTINCT). UNION ALL includes all rows including duplicates. UNION ALL is faster because it skips the deduplication step. Use UNION ALL when you know there are no duplicates or want them.",
    ),
    Question(
        id="sql_009", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What are subqueries and when would you use them?",
        expected_keywords=["subquery", "nested", "SELECT", "IN", "EXISTS", "correlated", "scalar", "derived table", "inner query"],
        model_answer_hint="Subqueries are queries nested inside another query. Types: scalar (returns one value), row, table. Used in WHERE (IN, EXISTS), FROM (derived tables), SELECT. Correlated subqueries reference the outer query. Can often be rewritten as JOINs.",
    ),
    Question(
        id="sql_010", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="Explain the SQL execution order of operations.",
        expected_keywords=["FROM", "WHERE", "GROUP BY", "HAVING", "SELECT", "ORDER BY", "LIMIT", "execution order", "logical"],
        model_answer_hint="Logical execution order: FROM (join tables) → WHERE (filter rows) → GROUP BY (group) → HAVING (filter groups) → SELECT (compute columns) → DISTINCT → ORDER BY → LIMIT/OFFSET. Written order differs from execution order.",
    ),
    Question(
        id="sql_011", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What are SQL constraints? Name the common types.",
        expected_keywords=["constraint", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "NOT NULL", "CHECK", "DEFAULT", "integrity"],
        model_answer_hint="Constraints enforce data integrity rules: PRIMARY KEY (unique + not null), FOREIGN KEY (referential integrity), UNIQUE (no duplicates), NOT NULL (required), CHECK (custom condition), DEFAULT (auto-fill value). Applied at column or table level.",
    ),
    Question(
        id="sql_012", topic="sql_basics", difficulty="easy", category="sql",
        question_type="technical",
        text="What is NULL in SQL and how do you handle it?",
        expected_keywords=["NULL", "unknown", "IS NULL", "IS NOT NULL", "COALESCE", "IFNULL", "three-valued", "comparison", "aggregate"],
        model_answer_hint="NULL represents unknown/missing data. Comparisons with NULL yield UNKNOWN (not TRUE/FALSE). Use IS NULL/IS NOT NULL for checks, COALESCE for defaults, NVL/IFNULL for substitution. Most aggregates ignore NULLs. NULL in math operations produces NULL.",
    ),
    # --- MEDIUM (16) ---
    Question(
        id="sql_013", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="Explain window functions in SQL. Give examples of ROW_NUMBER, RANK, and DENSE_RANK.",
        expected_keywords=["window", "OVER", "PARTITION BY", "ORDER BY", "ROW_NUMBER", "RANK", "DENSE_RANK", "frame", "running"],
        model_answer_hint="Window functions compute over a set of rows without collapsing them. OVER(PARTITION BY... ORDER BY...). ROW_NUMBER: unique sequential. RANK: same rank for ties, skips next. DENSE_RANK: same rank for ties, no skip. Also: LAG, LEAD, SUM OVER, running totals.",
    ),
    Question(
        id="sql_014", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="What are CTEs (Common Table Expressions) and recursive CTEs?",
        expected_keywords=["CTE", "WITH", "readable", "recursive", "hierarchy", "anchor", "reuse", "temporary", "tree"],
        model_answer_hint="CTEs (WITH clause) create named temporary result sets for readability and reuse within a query. Recursive CTEs have anchor + recursive member joined by UNION ALL—useful for hierarchies (org charts, tree structures, bill of materials).",
    ),
    Question(
        id="sql_015", topic="sql_performance", difficulty="medium", category="sql",
        question_type="technical",
        text="How do you analyze and optimize a slow SQL query?",
        expected_keywords=["EXPLAIN", "execution plan", "index", "scan", "seek", "statistics", "join order", "covering index", "selectivity"],
        model_answer_hint="Use EXPLAIN/EXPLAIN ANALYZE to see execution plan. Look for: table scans (add indexes), poor join order, missing statistics, expensive sorts. Solutions: proper indexes, covering indexes, query rewriting, denormalization, materialized views. Check index selectivity.",
    ),
    Question(
        id="sql_016", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="Explain the ACID properties of database transactions.",
        expected_keywords=["Atomicity", "Consistency", "Isolation", "Durability", "transaction", "commit", "rollback", "guarantee"],
        model_answer_hint="Atomicity: all-or-nothing (commit/rollback). Consistency: database moves between valid states. Isolation: concurrent transactions don't interfere. Durability: committed data survives system failure. These properties ensure reliable database operations.",
    ),
    Question(
        id="sql_017", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="What are the different transaction isolation levels?",
        expected_keywords=["READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE", "dirty read", "phantom", "non-repeatable"],
        model_answer_hint="READ UNCOMMITTED: allows dirty reads. READ COMMITTED: sees only committed data. REPEATABLE READ: no non-repeatable reads. SERIALIZABLE: full isolation, prevents phantoms. Higher isolation = more locking/overhead = less concurrency. Most databases default to READ COMMITTED.",
    ),
    Question(
        id="sql_018", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="How do you design a database schema for a many-to-many relationship?",
        expected_keywords=["junction table", "join table", "many-to-many", "foreign key", "composite key", "bridge table", "pivot", "relationship"],
        model_answer_hint="Use a junction/bridge table with foreign keys to both related tables. Primary key can be composite (both FKs) or surrogate. Add additional columns for relationship attributes (e.g., enrollment date in student-course). Create indexes on FK columns.",
    ),
    Question(
        id="sql_019", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="What are stored procedures and triggers? When should you use them?",
        expected_keywords=["stored procedure", "trigger", "encapsulate", "performance", "server-side", "automatic", "event", "INSERT", "UPDATE", "logic"],
        model_answer_hint="Stored procedures: precompiled SQL blocks for reusable logic, reduce network round-trips. Triggers: automatic execution on INSERT/UPDATE/DELETE events. Use procedures for complex business logic. Triggers for audit logs, data validation, cascading updates. Avoid complex trigger chains.",
    ),
    Question(
        id="sql_020", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="Explain the difference between optimistic and pessimistic locking.",
        expected_keywords=["optimistic", "pessimistic", "lock", "version", "conflict", "concurrent", "row lock", "table lock", "contention"],
        model_answer_hint="Pessimistic: lock rows/tables before modification (SELECT FOR UPDATE), blocks others. Optimistic: no locks, check version/timestamp at write time, retry on conflict. Optimistic better for low-contention scenarios, pessimistic for high-contention critical operations.",
    ),
    Question(
        id="sql_021", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="How would you implement pagination in SQL efficiently?",
        expected_keywords=["OFFSET", "LIMIT", "cursor", "keyset", "pagination", "performance", "seek", "index", "large dataset"],
        model_answer_hint="OFFSET/LIMIT: simple but slow for large offsets (scans skipped rows). Keyset/cursor pagination: use WHERE id > last_seen_id ORDER BY id LIMIT n—uses index, consistent performance. Keyset is preferred for large datasets but requires stable sort column.",
    ),
    Question(
        id="sql_022", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="What is denormalization and when is it appropriate?",
        expected_keywords=["denormalization", "redundancy", "performance", "read-heavy", "join", "trade-off", "materialized view", "cache"],
        model_answer_hint="Denormalization intentionally adds redundancy to improve read performance by avoiding joins. Appropriate for read-heavy workloads, reporting, data warehouses. Trade-offs: write complexity, data inconsistency risk. Alternatives: materialized views, caching layers.",
    ),
    Question(
        id="sql_023", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="Explain different index types: B-tree, Hash, GiST, and Full-text.",
        expected_keywords=["B-tree", "hash", "GiST", "full-text", "range", "equality", "spatial", "text search", "composite"],
        model_answer_hint="B-tree: default, supports range queries and equality (most versatile). Hash: equality-only, faster for exact matches. GiST: generalized search for spatial/geometric data. Full-text: text search with relevance ranking. Choose based on query patterns.",
    ),
    Question(
        id="sql_024", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="How do you handle hierarchical data in SQL?",
        expected_keywords=["adjacency list", "nested set", "materialized path", "closure table", "recursive CTE", "hierarchy", "parent", "tree"],
        model_answer_hint="Approaches: Adjacency List (parent_id column, simple but recursive queries), Nested Sets (left/right values, fast reads but expensive writes), Materialized Path (path string), Closure Table (ancestor/descendant pairs, balanced performance). Recursive CTEs help with adjacency list queries.",
    ),
    Question(
        id="sql_025", topic="sql_performance", difficulty="medium", category="sql",
        question_type="technical",
        text="What is a covering index and when should you use one?",
        expected_keywords=["covering index", "include", "all columns", "index-only scan", "lookup", "performance", "SELECT", "avoids"],
        model_answer_hint="A covering index includes all columns needed by a query, enabling index-only scans without accessing the main table. Created with INCLUDE clause or adding columns to the index. Eliminates random I/O lookups. Best for frequently-run queries with specific column patterns.",
    ),
    Question(
        id="sql_026", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="What are materialized views and when would you use them?",
        expected_keywords=["materialized view", "precomputed", "refresh", "performance", "aggregation", "stale", "trade-off", "scheduled"],
        model_answer_hint="Materialized views store precomputed query results physically. Used for expensive aggregations, reporting queries, data warehousing. Must be refreshed (scheduled or on-demand). Trade-off: faster reads vs. storage + staleness. Some DBs support incremental refresh.",
    ),
    Question(
        id="sql_027", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="How do you detect and resolve deadlocks?",
        expected_keywords=["deadlock", "cycle", "lock", "wait-for graph", "timeout", "retry", "order", "detection", "prevention"],
        model_answer_hint="Deadlocks: circular wait between transactions. Detection: wait-for graph, timeout-based. Resolution: kill one transaction (victim selection by cost). Prevention: consistent lock ordering, shorter transactions, use NOWAIT/SKIP LOCKED, implement retry logic in application.",
    ),
    Question(
        id="sql_028", topic="sql_advanced", difficulty="medium", category="sql",
        question_type="technical",
        text="Explain the difference between vertical and horizontal partitioning (sharding).",
        expected_keywords=["vertical", "horizontal", "partition", "shard", "distribute", "range", "hash", "list", "scalability"],
        model_answer_hint="Vertical partitioning: split columns into separate tables (normalize). Horizontal partitioning/sharding: split rows across tables/servers by key (range, hash, list). Sharding enables horizontal scaling. Challenges: cross-shard queries, consistency, rebalancing.",
    ),
    # --- HARD (12) ---
    Question(
        id="sql_029", topic="sql_performance", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you design a database schema for a high-throughput time-series application?",
        expected_keywords=["time-series", "partition", "compression", "retention", "hypertable", "TimescaleDB", "downsampling", "write-optimized", "chunks"],
        model_answer_hint="Time-partition tables (by day/week), write-optimized storage (append-only), compression for old data, retention policies for deletion, downsampling for aggregates, consider TimescaleDB/InfluxDB. Index on time + entity. Batch inserts. Continuous aggregates for queries.",
    ),
    Question(
        id="sql_030", topic="sql_performance", difficulty="hard", category="sql",
        question_type="technical",
        text="Explain Multi-Version Concurrency Control (MVCC) and its implementation.",
        expected_keywords=["MVCC", "version", "snapshot", "visibility", "vacuum", "undo log", "timestamp", "concurrent", "read without lock"],
        model_answer_hint="MVCC keeps multiple versions of rows. Readers see a consistent snapshot without locking writers. PostgreSQL: stores versions in heap, uses transaction IDs for visibility checks, VACUUM removes dead tuples. MySQL InnoDB: uses undo logs for older versions. Enables high concurrency.",
    ),
    Question(
        id="sql_031", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="How would you design a database for a multi-tenant SaaS application?",
        expected_keywords=["multi-tenant", "schema", "shared database", "row-level security", "tenant_id", "isolation", "performance", "scalability", "migration"],
        model_answer_hint="Approaches: shared database with tenant_id column (simplest, RLS for isolation), schema-per-tenant (better isolation, harder migration), database-per-tenant (best isolation, most overhead). Most use shared + RLS. Add tenant_id to all indexes. Consider noisy neighbor prevention.",
    ),
    Question(
        id="sql_032", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you implement eventually consistent distributed transactions across microservices?",
        expected_keywords=["saga", "event sourcing", "compensating", "distributed transaction", "2PC", "outbox", "choreography", "orchestration", "idempotent"],
        model_answer_hint="Saga pattern: sequence of local transactions with compensating actions for rollback. Choreography (events) vs. Orchestration (coordinator). Outbox pattern for reliable event publishing. Ensure idempotency. Avoid 2PC for performance. Accept eventual consistency with conflict resolution.",
    ),
    Question(
        id="sql_033", topic="sql_performance", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you optimize a query that joins 10+ tables with millions of rows each?",
        expected_keywords=["execution plan", "statistics", "join order", "index", "partition", "materialized", "denormalize", "parallel", "hints"],
        model_answer_hint="Analyze execution plan, ensure statistics are updated, verify proper indexes on join columns, consider join order hints, partition large tables, pre-aggregate into materialized views, denormalize hot paths, use parallel query execution, reduce result set early with WHERE pushdown.",
    ),
    Question(
        id="sql_034", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="Explain the CAP theorem and its implications for distributed databases.",
        expected_keywords=["CAP", "Consistency", "Availability", "Partition tolerance", "distributed", "trade-off", "CP", "AP", "eventual"],
        model_answer_hint="CAP: distributed systems can guarantee at most 2 of 3: Consistency (all nodes see same data), Availability (every request gets response), Partition tolerance (works despite network splits). In practice, must choose CP (strong consistency, may reject requests) or AP (always available, eventually consistent).",
    ),
    Question(
        id="sql_035", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="How does a query optimizer work? Explain cost-based optimization.",
        expected_keywords=["cost-based", "optimizer", "statistics", "cardinality", "selectivity", "plan", "scan", "join algorithm", "histogram"],
        model_answer_hint="Cost-based optimizer estimates cost of different execution plans using statistics (cardinality estimates from histograms, selectivity). Considers: scan methods (seq vs index), join algorithms (nested loop, hash, merge), join order. Chooses plan with lowest estimated I/O + CPU cost.",
    ),
    Question(
        id="sql_036", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="Design a database schema for a social media feed with billions of posts.",
        expected_keywords=["fan-out", "timeline", "sharding", "cache", "partition", "denormalize", "read/write", "materialized", "user_id"],
        model_answer_hint="Options: fan-out on write (precompute timelines), fan-out on read (query at request time). Hybrid: fan-out on write for normal users, read for celebrities. Shard by user_id, partition posts by time, Redis cache for hot timelines, denormalize author info into posts.",
    ),
    Question(
        id="sql_037", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you implement Change Data Capture (CDC) and what are its use cases?",
        expected_keywords=["CDC", "change data capture", "log-based", "trigger-based", "Debezium", "replication", "event", "streaming", "WAL"],
        model_answer_hint="CDC captures row-level changes. Methods: log-based (read WAL/binlog—Debezium), trigger-based (custom triggers write changes), polling. Use for: event-driven architecture, cache invalidation, search index sync, data warehousing, audit. Log-based is lowest overhead and most reliable.",
    ),
    Question(
        id="sql_038", topic="sql_performance", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you handle database migrations in a zero-downtime deployment?",
        expected_keywords=["zero-downtime", "migration", "backward compatible", "expand-contract", "blue-green", "rolling", "online DDL", "shadow"],
        model_answer_hint="Expand-contract pattern: 1) Add new column/table (expand), 2) Deploy app reading both, 3) Backfill data, 4) Deploy app using only new, 5) Remove old (contract). Use online DDL (no locks), feature flags for transition. Never rename/drop columns in one step. Ghost/pt-online-schema-change tools.",
    ),
    Question(
        id="sql_039", topic="sql_advanced", difficulty="hard", category="sql",
        question_type="technical",
        text="Explain the trade-offs between SQL and NoSQL for different use cases.",
        expected_keywords=["SQL", "NoSQL", "schema", "scalability", "consistency", "flexibility", "ACID", "BASE", "use case", "document", "graph"],
        model_answer_hint="SQL: strong consistency, complex queries, structured data, ACID. NoSQL: flexible schema, horizontal scaling, high write throughput, eventual consistency. Document DB for varied structures, Graph for relationships, Key-value for caching, Column-family for time-series. Choose based on access patterns.",
    ),
    Question(
        id="sql_040", topic="sql_performance", difficulty="hard", category="sql",
        question_type="technical",
        text="How do you implement database connection pooling and why is it important?",
        expected_keywords=["connection pool", "overhead", "reuse", "limit", "pgbouncer", "HikariCP", "timeout", "idle", "concurrency"],
        model_answer_hint="Connection pooling reuses database connections to avoid expensive creation overhead (TCP handshake, auth, memory allocation per connection). Tools: PgBouncer (PostgreSQL), HikariCP (Java). Configure: max pool size, idle timeout, connection lifetime. Transaction vs session pooling modes.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# AWS QUESTIONS (30)
# ═══════════════════════════════════════════════════════════════════════════════

AWS_QUESTIONS = [
    # --- EASY (8) ---
    Question(
        id="aws_001", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What are the main differences between EC2, Lambda, and ECS?",
        expected_keywords=["EC2", "Lambda", "ECS", "virtual machine", "serverless", "container", "scaling", "managed", "compute"],
        model_answer_hint="EC2: virtual machines (full control, manual scaling). Lambda: serverless functions (event-driven, auto-scale, pay per invocation). ECS: container orchestration (Docker, managed cluster). Choose based on control needs, traffic patterns, and operational overhead preference.",
    ),
    Question(
        id="aws_002", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="Explain S3 storage classes and when to use each.",
        expected_keywords=["Standard", "IA", "Glacier", "One Zone", "Intelligent-Tiering", "lifecycle", "cost", "access frequency"],
        model_answer_hint="Standard: frequently accessed. Standard-IA: infrequent access, lower cost. One Zone-IA: same but single AZ. Glacier: archive (minutes-hours retrieval). Glacier Deep Archive: cheapest, hours retrieval. Intelligent-Tiering: auto-moves based on access patterns. Use lifecycle policies.",
    ),
    Question(
        id="aws_003", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What is a VPC and what are its core components?",
        expected_keywords=["VPC", "subnet", "route table", "internet gateway", "NAT", "security group", "NACL", "CIDR", "public", "private"],
        model_answer_hint="VPC is an isolated virtual network. Components: subnets (public/private), route tables (traffic rules), internet gateway (public access), NAT gateway (private subnet outbound), security groups (stateful firewall), NACLs (stateless firewall). CIDR defines IP range.",
    ),
    Question(
        id="aws_004", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What is IAM and how does it work?",
        expected_keywords=["IAM", "user", "role", "policy", "permission", "group", "least privilege", "JSON", "assume role"],
        model_answer_hint="IAM manages access control. Users (people), Groups (collection of users), Roles (assumed by services/users), Policies (JSON permission documents). Follow least privilege principle. Policies define Allow/Deny for actions on resources with optional conditions.",
    ),
    Question(
        id="aws_005", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What is the difference between Security Groups and NACLs?",
        expected_keywords=["security group", "NACL", "stateful", "stateless", "allow", "deny", "instance", "subnet", "inbound", "outbound"],
        model_answer_hint="Security Groups: stateful (return traffic auto-allowed), instance-level, allow rules only, evaluate all rules. NACLs: stateless (must explicitly allow return traffic), subnet-level, allow AND deny rules, rules evaluated in order. Use both for defense in depth.",
    ),
    Question(
        id="aws_006", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="Explain the difference between RDS and DynamoDB.",
        expected_keywords=["RDS", "DynamoDB", "relational", "NoSQL", "SQL", "managed", "scaling", "schema", "key-value", "document"],
        model_answer_hint="RDS: managed relational databases (MySQL, PostgreSQL, etc.), SQL queries, ACID, vertical scaling. DynamoDB: managed NoSQL (key-value/document), single-digit ms latency, unlimited horizontal scaling, flexible schema. RDS for complex queries, DynamoDB for high-scale simple access patterns.",
    ),
    Question(
        id="aws_007", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What is CloudWatch and what can you monitor with it?",
        expected_keywords=["CloudWatch", "metrics", "alarms", "logs", "dashboard", "monitoring", "custom metrics", "retention", "trigger"],
        model_answer_hint="CloudWatch collects metrics, logs, and events from AWS services. Features: dashboards for visualization, alarms to trigger actions (SNS, Auto Scaling), log groups for centralized logging, custom metrics for application data. Supports metric math and anomaly detection.",
    ),
    Question(
        id="aws_008", topic="aws_basics", difficulty="easy", category="aws",
        question_type="technical",
        text="What is Auto Scaling and how does it work?",
        expected_keywords=["Auto Scaling", "launch template", "scaling policy", "target tracking", "min", "max", "desired", "health check", "metric"],
        model_answer_hint="Auto Scaling automatically adjusts EC2 instance count based on demand. Components: launch template (instance config), scaling policies (rules). Types: target tracking (maintain metric), step scaling, scheduled. Configure min/max/desired capacity. Health checks replace unhealthy instances.",
    ),
    # --- MEDIUM (12) ---
    Question(
        id="aws_009", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="Design a highly available web application architecture on AWS.",
        expected_keywords=["multi-AZ", "ALB", "Auto Scaling", "RDS replica", "S3", "CloudFront", "Route53", "health check", "failover"],
        model_answer_hint="Multi-AZ deployment: ALB distributing to Auto Scaling group across AZs, RDS Multi-AZ with read replicas, S3 for static assets, CloudFront CDN, Route53 for DNS with health checks and failover. ElastiCache for session/caching. Separate public/private subnets.",
    ),
    Question(
        id="aws_010", topic="aws_serverless", difficulty="medium", category="aws",
        question_type="technical",
        text="How would you build a serverless API with Lambda and API Gateway?",
        expected_keywords=["Lambda", "API Gateway", "DynamoDB", "IAM role", "CORS", "stage", "throttling", "cold start", "event"],
        model_answer_hint="API Gateway defines REST/HTTP endpoints, routes to Lambda functions. Lambda handles business logic, talks to DynamoDB/other services. IAM roles for permissions. Handle CORS, set throttling/quotas. Stages for environments. Address cold starts with provisioned concurrency or smaller runtimes.",
    ),
    Question(
        id="aws_011", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="Explain the event-driven architecture pattern with SQS, SNS, and EventBridge.",
        expected_keywords=["SQS", "SNS", "EventBridge", "decouple", "event", "queue", "topic", "fan-out", "dead letter", "retry"],
        model_answer_hint="SNS: pub/sub fan-out (one event → many subscribers). SQS: message queue (reliable, decoupled processing, DLQ for failures). EventBridge: event bus with rules and routing. Pattern: producer → SNS/EventBridge → SQS queues → consumers. Dead letter queues for failed messages. Enables loose coupling.",
    ),
    Question(
        id="aws_012", topic="aws_security", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you secure data at rest and in transit on AWS?",
        expected_keywords=["KMS", "encryption", "SSL/TLS", "at rest", "in transit", "CMK", "envelope", "S3 encryption", "certificate"],
        model_answer_hint="At rest: KMS managed keys (CMK), S3 server-side encryption (SSE-S3, SSE-KMS), EBS encryption, RDS encryption. In transit: TLS/SSL everywhere, ACM for certificates, ALB HTTPS termination. Envelope encryption for client-side. VPC endpoints to avoid internet transit.",
    ),
    Question(
        id="aws_013", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you implement CI/CD on AWS?",
        expected_keywords=["CodePipeline", "CodeBuild", "CodeDeploy", "ECR", "blue-green", "rolling", "canary", "artifact", "automated"],
        model_answer_hint="CodePipeline orchestrates stages. CodeBuild compiles/tests (buildspec.yml). CodeDeploy deploys to EC2/ECS/Lambda (blue-green, rolling, canary strategies). ECR for Docker images. Or use GitHub Actions with AWS credentials. Implement automated testing, approval gates, rollback.",
    ),
    Question(
        id="aws_014", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="What is Infrastructure as Code and how do you use Terraform/CloudFormation?",
        expected_keywords=["IaC", "Terraform", "CloudFormation", "declarative", "state", "drift", "module", "template", "reproducible"],
        model_answer_hint="IaC defines infrastructure in code files: reproducible, version-controlled, reviewable. CloudFormation: AWS-native, YAML/JSON templates, nested stacks. Terraform: multi-cloud, HCL, state files, modules, providers. Both support drift detection, change planning (plan/changeset), and rollback.",
    ),
    Question(
        id="aws_015", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you implement microservices communication patterns on AWS?",
        expected_keywords=["synchronous", "asynchronous", "API Gateway", "SQS", "gRPC", "service mesh", "App Mesh", "event-driven", "circuit breaker"],
        model_answer_hint="Synchronous: API Gateway, ALB, gRPC (for internal). Asynchronous: SQS queues, SNS topics, EventBridge. Service mesh (App Mesh/Envoy) for observability and traffic control. Patterns: API Gateway for external, event-driven for internal, circuit breaker for resilience.",
    ),
    Question(
        id="aws_016", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="Explain ECS vs EKS. When would you choose one over the other?",
        expected_keywords=["ECS", "EKS", "Kubernetes", "Docker", "Fargate", "complexity", "portability", "ecosystem", "task definition"],
        model_answer_hint="ECS: AWS-native container orchestration, simpler, tight AWS integration, task definitions. EKS: managed Kubernetes, portable, rich ecosystem (Helm, operators), steeper learning curve. Both support Fargate (serverless). Choose ECS for simplicity/AWS lock-in acceptable, EKS for K8s expertise/portability needs.",
    ),
    Question(
        id="aws_017", topic="aws_data", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you design a data lake on AWS?",
        expected_keywords=["S3", "Glue", "Athena", "Lake Formation", "Parquet", "partitioning", "catalog", "ETL", "zone"],
        model_answer_hint="S3 as storage layer (raw/processed/curated zones). AWS Glue for ETL and catalog. Athena for serverless SQL queries. Lake Formation for governance/permissions. Use Parquet/ORC columnar formats, partition by date/key fields. Implement data quality checks and lineage tracking.",
    ),
    Question(
        id="aws_018", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you implement caching strategies on AWS?",
        expected_keywords=["ElastiCache", "Redis", "Memcached", "CloudFront", "DAX", "TTL", "invalidation", "cache-aside", "write-through"],
        model_answer_hint="Layers: CloudFront (CDN edge), API Gateway cache, ElastiCache (Redis/Memcached) for application, DAX for DynamoDB. Patterns: cache-aside (app manages), write-through (write to cache + DB), write-behind (async DB write). Set appropriate TTLs, implement cache invalidation.",
    ),
    Question(
        id="aws_019", topic="aws_security", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you implement least-privilege access with IAM?",
        expected_keywords=["least privilege", "policy", "condition", "boundary", "SCP", "role", "assume", "resource-based", "audit"],
        model_answer_hint="Start with no permissions, add only what's needed. Use IAM Access Analyzer to identify unused permissions. Implement permission boundaries for developers. SCPs for organizational guardrails. Use conditions (IP, MFA, time). Regular access reviews. Prefer roles over long-term credentials.",
    ),
    Question(
        id="aws_020", topic="aws_architecture", difficulty="medium", category="aws",
        question_type="technical",
        text="How do you handle secrets and configuration management on AWS?",
        expected_keywords=["Secrets Manager", "SSM Parameter Store", "rotation", "encryption", "KMS", "environment", "IAM", "access control"],
        model_answer_hint="Secrets Manager: for credentials with automatic rotation. SSM Parameter Store: for configuration (free tier, hierarchical). Both encrypt with KMS. Access via IAM policies. Never hardcode secrets. Use environment variables or SDK to fetch at runtime. Enable audit logging.",
    ),
    # --- HARD (10) ---
    Question(
        id="aws_021", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="Design a multi-region active-active architecture for a global application.",
        expected_keywords=["multi-region", "active-active", "Route53", "DynamoDB Global Tables", "conflict resolution", "latency routing", "replication", "eventual consistency"],
        model_answer_hint="Route53 latency-based routing to regional ALBs. DynamoDB Global Tables for multi-region data replication. Conflict resolution (last-writer-wins or application-level). S3 cross-region replication. CloudFront for static. Regional failover. Accept eventual consistency. Handle data sovereignty requirements.",
    ),
    Question(
        id="aws_022", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="How do you design a system to handle 1 million requests per second on AWS?",
        expected_keywords=["horizontal scaling", "caching", "CDN", "sharding", "async", "queue", "pre-computation", "edge", "stateless"],
        model_answer_hint="CloudFront/edge caching for static content, ALB + Auto Scaling for compute, Redis cluster for hot data, DynamoDB with DAX, SQS for write buffering, pre-compute where possible, stateless services, database sharding, connection pooling. Design for failures at each layer.",
    ),
    Question(
        id="aws_023", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="How would you implement a real-time data streaming pipeline on AWS?",
        expected_keywords=["Kinesis", "Firehose", "Lambda", "stream processing", "partitioning", "scaling", "ordering", "exactly-once", "analytics"],
        model_answer_hint="Kinesis Data Streams for ingestion (partition by key for ordering), Lambda or Kinesis Analytics for real-time processing, Firehose for delivery to S3/Redshift/ES. Handle deduplication, ordering within partitions, scaling shards. Consider MSK (Kafka) for complex streaming needs.",
    ),
    Question(
        id="aws_024", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="Explain how to implement disaster recovery strategies on AWS (RTO/RPO).",
        expected_keywords=["RTO", "RPO", "backup-restore", "pilot light", "warm standby", "multi-site", "replication", "recovery", "cost"],
        model_answer_hint="Strategies by cost/speed: Backup & Restore (cheap, high RTO/RPO), Pilot Light (minimal always-on, moderate RTO), Warm Standby (scaled-down active, low RTO), Multi-Site Active-Active (lowest RTO/RPO, highest cost). Choose based on business requirements. Test regularly with chaos engineering.",
    ),
    Question(
        id="aws_025", topic="aws_cost", difficulty="hard", category="aws",
        question_type="technical",
        text="How do you optimize AWS costs for a large-scale application?",
        expected_keywords=["Reserved Instances", "Spot", "Savings Plans", "right-sizing", "auto-scaling", "S3 lifecycle", "Cost Explorer", "tagging", "FinOps"],
        model_answer_hint="Reserved Instances/Savings Plans for stable workloads (up to 72% savings). Spot for fault-tolerant workloads. Right-size instances (Compute Optimizer). S3 lifecycle policies. Auto-scaling to match demand. Use Cost Explorer and budgets. Tag everything for allocation. Graviton instances for better price/performance.",
    ),
    Question(
        id="aws_026", topic="aws_security", difficulty="hard", category="aws",
        question_type="technical",
        text="How do you implement a zero-trust security model on AWS?",
        expected_keywords=["zero trust", "verify", "least privilege", "microsegmentation", "identity", "mTLS", "VPC endpoints", "logging", "continuous"],
        model_answer_hint="Never trust, always verify: strong identity (IAM + MFA everywhere), microsegmentation (SGs per workload), mTLS between services, VPC endpoints (no internet traversal), continuous monitoring (GuardDuty, Security Hub), encryption everywhere, assume breach mentality, just-in-time access.",
    ),
    Question(
        id="aws_027", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="How do you handle data consistency in a distributed microservices architecture on AWS?",
        expected_keywords=["saga", "eventual consistency", "idempotent", "outbox", "CDC", "compensation", "DynamoDB streams", "SQS", "exactly-once"],
        model_answer_hint="Accept eventual consistency. Implement saga pattern (SQS/Step Functions for orchestration). Outbox pattern for reliable event publishing. DynamoDB Streams for CDC. Idempotent consumers. Compensating transactions for rollback. Use Step Functions for complex workflows with error handling.",
    ),
    Question(
        id="aws_028", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="Design a machine learning pipeline on AWS from data ingestion to model serving.",
        expected_keywords=["SageMaker", "S3", "Glue", "feature store", "training", "endpoint", "pipeline", "monitoring", "A/B testing", "MLOps"],
        model_answer_hint="Data: S3 data lake → Glue ETL → Feature Store. Training: SageMaker training jobs, hyperparameter tuning, experiments. Deployment: SageMaker endpoints with auto-scaling, A/B testing. MLOps: SageMaker Pipelines for CI/CD, Model Monitor for drift detection, Model Registry for versioning.",
    ),
    Question(
        id="aws_029", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="How would you migrate a monolithic application to microservices on AWS?",
        expected_keywords=["strangler fig", "decompose", "bounded context", "API Gateway", "migration", "incremental", "DDD", "event", "database per service"],
        model_answer_hint="Strangler Fig pattern: incrementally extract services behind API Gateway. Identify bounded contexts (DDD). Database per service with eventual consistency. Start with least coupled modules. Use events for integration. Keep monolith running during migration. Feature flags for gradual traffic shift.",
    ),
    Question(
        id="aws_030", topic="aws_architecture", difficulty="hard", category="aws",
        question_type="technical",
        text="How do you implement observability (not just monitoring) in a distributed AWS architecture?",
        expected_keywords=["traces", "metrics", "logs", "X-Ray", "CloudWatch", "OpenTelemetry", "correlation ID", "distributed tracing", "SLO", "alerting"],
        model_answer_hint="Three pillars: Metrics (CloudWatch custom metrics, percentiles), Logs (structured JSON, correlation IDs, CloudWatch Logs Insights), Traces (X-Ray/OpenTelemetry for distributed tracing). Define SLOs/SLIs, alert on SLO burn rate. Dashboards per service. Trace ID propagation across services.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER/KUBERNETES QUESTIONS (25)
# ═══════════════════════════════════════════════════════════════════════════════

DOCKER_QUESTIONS = [
    # --- EASY (7) ---
    Question(
        id="docker_001", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="What is Docker and how is it different from virtual machines?",
        expected_keywords=["container", "image", "lightweight", "kernel", "isolation", "VM", "hypervisor", "OS", "faster", "portable"],
        model_answer_hint="Docker runs containers that share the host OS kernel—lightweight, fast startup, less overhead. VMs run full guest OS on hypervisor—stronger isolation, more resource usage. Containers are portable, consistent across environments. VMs provide hardware-level isolation.",
    ),
    Question(
        id="docker_002", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="Explain the difference between a Docker image and a container.",
        expected_keywords=["image", "container", "template", "running", "layer", "read-only", "instance", "process", "writable"],
        model_answer_hint="Image: read-only template with app + dependencies (built from Dockerfile, composed of layers). Container: running instance of an image (adds writable layer on top). Multiple containers can run from one image. Images are built, containers are runtime.",
    ),
    Question(
        id="docker_003", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="What is a Dockerfile and what are common instructions?",
        expected_keywords=["FROM", "COPY", "RUN", "CMD", "EXPOSE", "ENV", "WORKDIR", "ENTRYPOINT", "layer", "build"],
        model_answer_hint="Dockerfile defines how to build an image. Key instructions: FROM (base image), COPY/ADD (add files), RUN (execute commands, creates layers), WORKDIR (set directory), ENV (environment), EXPOSE (document ports), CMD/ENTRYPOINT (default command).",
    ),
    Question(
        id="docker_004", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="What is Docker Compose and when would you use it?",
        expected_keywords=["compose", "multi-container", "YAML", "service", "network", "volume", "orchestration", "development", "define"],
        model_answer_hint="Docker Compose defines multi-container applications in a YAML file. Services, networks, and volumes in one file. Use for local development environments (app + DB + cache), testing, single-host deployments. 'docker compose up' starts everything.",
    ),
    Question(
        id="docker_005", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="How do Docker volumes work and why are they important?",
        expected_keywords=["volume", "persist", "data", "container", "mount", "bind mount", "named volume", "ephemeral", "storage"],
        model_answer_hint="Volumes persist data beyond container lifecycle (containers are ephemeral). Types: named volumes (Docker-managed), bind mounts (host path). Volumes are preferred for databases, shared data between containers. Data in container's writable layer is lost when container is removed.",
    ),
    Question(
        id="docker_006", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="What are Docker networks and the different network drivers?",
        expected_keywords=["bridge", "host", "overlay", "network", "driver", "isolation", "container", "communication", "DNS"],
        model_answer_hint="Docker networks enable container communication. Bridge: default, containers on same host. Host: no isolation, uses host networking. Overlay: multi-host networking (Swarm/K8s). None: no networking. Containers on same network can communicate by service name (built-in DNS).",
    ),
    Question(
        id="docker_007", topic="docker_basics", difficulty="easy", category="docker",
        question_type="technical",
        text="What is a Docker registry and how do you use it?",
        expected_keywords=["registry", "Docker Hub", "push", "pull", "image", "tag", "repository", "private", "ECR"],
        model_answer_hint="Registries store Docker images. Docker Hub is the public default. Private registries (AWS ECR, GCR, Harbor) for organizations. Use: docker build → docker tag → docker push to publish. docker pull to download. Tag images with versions for traceability.",
    ),
    # --- MEDIUM (10) ---
    Question(
        id="docker_008", topic="docker_advanced", difficulty="medium", category="docker",
        question_type="technical",
        text="How do you optimize Docker image size and build time?",
        expected_keywords=["multi-stage", "alpine", "layer caching", ".dockerignore", "minimize layers", "slim", "order", "dependencies first"],
        model_answer_hint="Multi-stage builds (build in one stage, copy artifact to minimal runtime stage). Use alpine/slim base images. Leverage layer caching (copy package files first, install deps, then copy source). .dockerignore to exclude files. Combine RUN commands. Remove caches/temp files.",
    ),
    Question(
        id="docker_009", topic="docker_security", difficulty="medium", category="docker",
        question_type="technical",
        text="What are Docker security best practices?",
        expected_keywords=["non-root", "USER", "scan", "minimal image", "secrets", "read-only", "capabilities", "trusted base", "limit resources"],
        model_answer_hint="Run as non-root user (USER directive). Use minimal base images. Scan for vulnerabilities (Trivy, Snyk). Don't store secrets in images. Use read-only file systems. Drop unnecessary Linux capabilities. Limit resources (memory, CPU). Pin base image versions. Use trusted registries.",
    ),
    Question(
        id="docker_010", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="Explain the core Kubernetes architecture: master and worker nodes.",
        expected_keywords=["control plane", "API server", "etcd", "scheduler", "controller manager", "kubelet", "kube-proxy", "pod", "node"],
        model_answer_hint="Control plane: API server (entry point), etcd (cluster state store), scheduler (pod placement), controller manager (reconciliation loops). Worker nodes: kubelet (manages pods), kube-proxy (networking), container runtime. Users interact via kubectl → API server.",
    ),
    Question(
        id="docker_011", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="What is a Pod in Kubernetes and how does it differ from a container?",
        expected_keywords=["Pod", "container", "smallest unit", "shared", "namespace", "network", "storage", "sidecar", "co-located"],
        model_answer_hint="Pod is the smallest deployable unit in K8s—wraps one or more containers sharing network namespace (same IP, localhost communication) and volumes. Co-located containers (sidecars) for logging, proxies. Pods are ephemeral. Don't deploy pods directly—use Deployments.",
    ),
    Question(
        id="docker_012", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="Explain Kubernetes Services: ClusterIP, NodePort, and LoadBalancer.",
        expected_keywords=["Service", "ClusterIP", "NodePort", "LoadBalancer", "Ingress", "stable IP", "discovery", "selector", "endpoint"],
        model_answer_hint="Services provide stable networking for Pods. ClusterIP: internal-only stable IP. NodePort: exposes on each node's IP at static port. LoadBalancer: provisions cloud LB (external access). Ingress: HTTP routing rules (path/host-based). Services use label selectors to find Pods.",
    ),
    Question(
        id="docker_013", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="How does Kubernetes handle scaling and self-healing?",
        expected_keywords=["HPA", "VPA", "replica", "health check", "liveness", "readiness", "restart", "rollout", "ReplicaSet"],
        model_answer_hint="Self-healing: liveness probes detect crashes (restart container), readiness probes control traffic routing. Scaling: HPA (auto-scale pods on CPU/memory/custom metrics), VPA (resize pod resources), Cluster Autoscaler (add/remove nodes). Deployments manage ReplicaSets for rollouts/rollbacks.",
    ),
    Question(
        id="docker_014", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="What are ConfigMaps and Secrets in Kubernetes?",
        expected_keywords=["ConfigMap", "Secret", "environment", "volume", "configuration", "decouple", "base64", "encrypted", "mount"],
        model_answer_hint="ConfigMaps: store non-sensitive configuration (key-value, files). Secrets: store sensitive data (base64 encoded, optionally encrypted at rest). Both injected as environment variables or volume mounts. Decouple configuration from container images. Enable config changes without rebuilds.",
    ),
    Question(
        id="docker_015", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="Explain Kubernetes deployment strategies: rolling update, blue-green, canary.",
        expected_keywords=["rolling update", "blue-green", "canary", "strategy", "zero-downtime", "rollback", "maxSurge", "maxUnavailable", "traffic"],
        model_answer_hint="Rolling update: gradually replace old pods (maxSurge/maxUnavailable control pace). Blue-green: two full environments, switch traffic instantly. Canary: route small % of traffic to new version, monitor, gradually increase. K8s native rolling update; canary/blue-green need Ingress or service mesh.",
    ),
    Question(
        id="docker_016", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="How do you manage persistent storage in Kubernetes?",
        expected_keywords=["PersistentVolume", "PersistentVolumeClaim", "StorageClass", "dynamic provisioning", "reclaim", "access mode", "stateful"],
        model_answer_hint="PersistentVolumes (PV): cluster storage resources. PersistentVolumeClaims (PVC): user requests for storage. StorageClasses: dynamic provisioning templates. Access modes: ReadWriteOnce, ReadOnlyMany, ReadWriteMany. StatefulSets for stateful workloads (stable identity, ordered deployment).",
    ),
    Question(
        id="docker_017", topic="docker_advanced", difficulty="medium", category="docker",
        question_type="technical",
        text="How do you implement health checks in Docker and Kubernetes?",
        expected_keywords=["HEALTHCHECK", "liveness", "readiness", "startup", "probe", "HTTP", "TCP", "exec", "interval", "threshold"],
        model_answer_hint="Docker: HEALTHCHECK instruction (CMD, interval, timeout, retries). Kubernetes: liveness probe (restart on failure), readiness probe (remove from service), startup probe (slow-starting apps). Methods: HTTP GET, TCP socket, exec command. Configure initialDelay, period, failureThreshold.",
    ),
    # --- HARD (8) ---
    Question(
        id="docker_018", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement a service mesh with Istio on Kubernetes?",
        expected_keywords=["Istio", "sidecar", "Envoy", "mTLS", "traffic management", "observability", "circuit breaker", "virtual service", "destination rule"],
        model_answer_hint="Istio injects Envoy sidecar proxies into pods for transparent service-to-service communication. Features: automatic mTLS, traffic splitting (canary), circuit breaking, retry policies, distributed tracing, access policies. VirtualService for routing rules, DestinationRule for traffic policies.",
    ),
    Question(
        id="docker_019", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you secure a Kubernetes cluster?",
        expected_keywords=["RBAC", "network policy", "pod security", "admission controller", "audit", "secrets encryption", "image scanning", "least privilege"],
        model_answer_hint="RBAC for access control (least privilege), Network Policies for pod-to-pod traffic filtering, Pod Security Standards/Admission for restricting pod capabilities, encrypt secrets at rest, scan images (admission webhook), audit logging, rotate credentials, limit API server access, use namespaces for isolation.",
    ),
    Question(
        id="docker_020", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement GitOps with ArgoCD or Flux?",
        expected_keywords=["GitOps", "ArgoCD", "Flux", "reconciliation", "declarative", "git", "sync", "drift detection", "automated", "pull-based"],
        model_answer_hint="GitOps: Git as source of truth for cluster state. ArgoCD/Flux continuously reconcile cluster state with Git repo. Pull-based deployment (cluster pulls from Git, not push). Detect drift, auto-sync or manual approval. Versioned, auditable, rollback-friendly. Follows Kubernetes declarative model.",
    ),
    Question(
        id="docker_021", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you troubleshoot a pod stuck in CrashLoopBackOff?",
        expected_keywords=["CrashLoopBackOff", "logs", "describe", "events", "OOMKilled", "exit code", "probe", "resource limits", "debug"],
        model_answer_hint="Diagnosis steps: kubectl describe pod (check events, exit codes), kubectl logs (and --previous for crashed container), check OOMKilled (increase memory limits), verify probe configuration, check resource limits, inspect configuration/secrets mounting, use ephemeral debug containers. Common causes: missing config, wrong command, permission errors.",
    ),
    Question(
        id="docker_022", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement zero-downtime deployments in Kubernetes?",
        expected_keywords=["rolling update", "readiness probe", "preStop", "PDB", "graceful shutdown", "connection draining", "maxSurge", "lifecycle"],
        model_answer_hint="Proper readiness probes (don't receive traffic until ready). preStop lifecycle hook (sleep before SIGTERM for connection draining). PodDisruptionBudget (maintain minimum available). Rolling update strategy (maxSurge, maxUnavailable). Graceful shutdown handling in app (drain connections on SIGTERM).",
    ),
    Question(
        id="docker_023", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How would you design a multi-cluster Kubernetes strategy?",
        expected_keywords=["multi-cluster", "federation", "failover", "service mesh", "global load balancer", "centralized management", "consistency", "disaster recovery"],
        model_answer_hint="Approaches: active-active across regions, active-passive DR. Tools: Kubernetes Federation, Admiral, multi-cluster service mesh (Istio). Global load balancer for traffic routing. Centralized GitOps for consistent configuration. Challenges: data replication, DNS, cross-cluster service discovery, cost.",
    ),
    Question(
        id="docker_024", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement custom autoscaling based on application metrics in Kubernetes?",
        expected_keywords=["HPA", "custom metrics", "Prometheus", "adapter", "KEDA", "event-driven", "external metrics", "scaling policy", "stabilization"],
        model_answer_hint="Custom metrics HPA: deploy Prometheus + custom metrics adapter, expose app metrics, configure HPA to scale on custom metric. KEDA: event-driven autoscaling (scale from zero, multiple trigger types—SQS queue length, Kafka lag, custom). Configure scaling policies for behavior tuning (stabilization window, scale-up/down rate).",
    ),
    Question(
        id="docker_025", topic="docker_advanced", difficulty="hard", category="docker",
        question_type="technical",
        text="Explain container runtime interfaces and how containerd/CRI-O relate to Kubernetes.",
        expected_keywords=["CRI", "containerd", "CRI-O", "OCI", "runc", "runtime", "kubelet", "shim", "interface"],
        model_answer_hint="CRI (Container Runtime Interface): K8s standard for container runtimes. containerd: industry-standard runtime (Docker's core). CRI-O: lightweight CRI implementation for K8s. Both use OCI-compliant runc for actual container execution. Kubelet → CRI → containerd/CRI-O → runc → container. Docker was deprecated as K8s runtime; containerd remains.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MACHINE LEARNING QUESTIONS (40)
# ═══════════════════════════════════════════════════════════════════════════════

ML_QUESTIONS = [
    # --- EASY (12) ---
    Question(
        id="ml_001", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is the difference between supervised, unsupervised, and reinforcement learning?",
        expected_keywords=["supervised", "unsupervised", "reinforcement", "labeled", "unlabeled", "reward", "classification", "clustering", "agent"],
        model_answer_hint="Supervised: labeled data, predicts output (classification, regression). Unsupervised: no labels, finds patterns (clustering, dimensionality reduction). Reinforcement: agent learns via reward/penalty through interaction with environment. Semi-supervised combines labeled + unlabeled.",
    ),
    Question(
        id="ml_002", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="Explain overfitting and underfitting. How do you prevent them?",
        expected_keywords=["overfitting", "underfitting", "bias", "variance", "regularization", "validation", "complexity", "training", "generalization"],
        model_answer_hint="Overfitting: model memorizes training data (high variance, poor generalization). Underfitting: model too simple (high bias). Prevention: regularization (L1/L2), cross-validation, early stopping, more data, dropout, ensemble methods, simpler model architecture.",
    ),
    Question(
        id="ml_003", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What are precision, recall, and F1-score?",
        expected_keywords=["precision", "recall", "F1", "true positive", "false positive", "false negative", "trade-off", "threshold", "confusion matrix"],
        model_answer_hint="Precision: TP/(TP+FP)—of predicted positives, how many are correct. Recall: TP/(TP+FN)—of actual positives, how many were found. F1: harmonic mean of precision and recall. Trade-off controlled by threshold. Use precision when FP is costly, recall when FN is costly.",
    ),
    Question(
        id="ml_004", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is cross-validation and why is it important?",
        expected_keywords=["cross-validation", "k-fold", "train-test", "generalization", "overfitting", "variance", "evaluation", "split", "robust"],
        model_answer_hint="Cross-validation splits data into k folds, trains on k-1, validates on 1, rotates k times. Provides robust performance estimate, detects overfitting, reduces evaluation variance. Common: 5-fold, 10-fold. Stratified for imbalanced classes. More reliable than single train-test split.",
    ),
    Question(
        id="ml_005", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="Explain the bias-variance trade-off.",
        expected_keywords=["bias", "variance", "trade-off", "complexity", "error", "underfitting", "overfitting", "balance", "noise"],
        model_answer_hint="Bias: error from oversimplified assumptions (underfitting). Variance: error from sensitivity to training data fluctuations (overfitting). Total error = bias² + variance + irreducible noise. Increasing model complexity reduces bias but increases variance. Goal: find optimal balance.",
    ),
    Question(
        id="ml_006", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is gradient descent and how does it work?",
        expected_keywords=["gradient", "descent", "optimization", "learning rate", "minimum", "loss function", "step", "derivative", "convergence"],
        model_answer_hint="Gradient descent iteratively minimizes a loss function by moving in the direction of steepest descent (negative gradient). Learning rate controls step size. Variants: batch (all data), stochastic (one sample), mini-batch (subset). Can get stuck in local minima.",
    ),
    Question(
        id="ml_007", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is feature engineering and why is it important?",
        expected_keywords=["feature", "engineering", "representation", "domain knowledge", "transformation", "encoding", "scaling", "selection", "performance"],
        model_answer_hint="Feature engineering transforms raw data into better representations for models. Includes: encoding categoricals (one-hot, label), scaling numerics, creating interactions, aggregations, text vectorization, handling missing values. Often more impactful than model choice. Requires domain knowledge.",
    ),
    Question(
        id="ml_008", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is the difference between classification and regression?",
        expected_keywords=["classification", "regression", "categorical", "continuous", "discrete", "predict", "label", "value", "output"],
        model_answer_hint="Classification predicts discrete categories/labels (spam/not-spam, image classes). Regression predicts continuous numerical values (price, temperature). Different loss functions: cross-entropy for classification, MSE/MAE for regression. Some algorithms do both (decision trees, neural networks).",
    ),
    Question(
        id="ml_009", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="Explain decision trees and their advantages/disadvantages.",
        expected_keywords=["decision tree", "split", "entropy", "Gini", "interpretable", "overfitting", "pruning", "feature importance", "non-linear"],
        model_answer_hint="Decision trees split data on features at each node using criteria (Gini impurity, entropy/information gain). Advantages: interpretable, handles non-linear relationships, no scaling needed. Disadvantages: prone to overfitting, unstable. Solutions: pruning, ensemble methods (Random Forest, XGBoost).",
    ),
    Question(
        id="ml_010", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is regularization and what are L1 and L2 regularization?",
        expected_keywords=["regularization", "L1", "L2", "Lasso", "Ridge", "penalty", "overfitting", "sparsity", "weights", "complexity"],
        model_answer_hint="Regularization adds a penalty term to the loss function to prevent overfitting. L1 (Lasso): absolute value penalty, promotes sparsity (some weights become zero, feature selection). L2 (Ridge): squared penalty, shrinks weights uniformly. Elastic Net combines both. Controlled by lambda hyperparameter.",
    ),
    Question(
        id="ml_011", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is a confusion matrix and what metrics can you derive from it?",
        expected_keywords=["confusion matrix", "TP", "TN", "FP", "FN", "accuracy", "precision", "recall", "specificity", "actual vs predicted"],
        model_answer_hint="Confusion matrix shows actual vs predicted classifications: TP, TN, FP, FN. Derived metrics: accuracy (correct/total), precision (TP/TP+FP), recall (TP/TP+FN), specificity (TN/TN+FP), F1-score. Useful for understanding error types, especially with imbalanced classes.",
    ),
    Question(
        id="ml_012", topic="ml_basics", difficulty="easy", category="machine_learning",
        question_type="technical",
        text="What is the difference between bagging and boosting?",
        expected_keywords=["bagging", "boosting", "ensemble", "parallel", "sequential", "variance", "bias", "Random Forest", "XGBoost", "bootstrap"],
        model_answer_hint="Bagging: train multiple models on bootstrap samples in parallel, aggregate predictions (reduces variance). Example: Random Forest. Boosting: train models sequentially, each fixing predecessors' errors (reduces bias). Examples: XGBoost, AdaBoost. Bagging for unstable models, boosting for weak learners.",
    ),
    # --- MEDIUM (16) ---
    Question(
        id="ml_013", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain how Random Forest works and its hyperparameters.",
        expected_keywords=["Random Forest", "bagging", "decision tree", "bootstrap", "feature subset", "n_estimators", "max_depth", "out-of-bag", "ensemble"],
        model_answer_hint="Random Forest: ensemble of decision trees trained on bootstrap samples with random feature subsets at each split. Reduces overfitting through averaging. Key hyperparameters: n_estimators (number of trees), max_depth, min_samples_split, max_features. OOB score for validation. Handles high-dimensional data well.",
    ),
    Question(
        id="ml_014", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How does XGBoost work and why is it effective?",
        expected_keywords=["XGBoost", "gradient boosting", "regularization", "tree", "learning rate", "second-order", "pruning", "parallel", "missing values"],
        model_answer_hint="XGBoost: optimized gradient boosting with regularization (L1/L2 on leaf weights), second-order Taylor expansion for loss approximation, built-in handling of missing values, column subsampling, parallel tree construction, pruning with gain threshold. Effective due to regularization + speed + flexibility.",
    ),
    Question(
        id="ml_015", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain neural network architectures: CNN, RNN, and Transformer.",
        expected_keywords=["CNN", "RNN", "Transformer", "convolution", "recurrent", "attention", "sequence", "spatial", "self-attention", "LSTM"],
        model_answer_hint="CNN: convolutional filters for spatial patterns (images, local features). RNN/LSTM: sequential processing with memory (time series, text—but vanishing gradient issues). Transformer: self-attention for parallel sequence processing (dominant in NLP/vision now). Each suited to different data types.",
    ),
    Question(
        id="ml_016", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How do you handle imbalanced datasets in machine learning?",
        expected_keywords=["imbalanced", "SMOTE", "oversampling", "undersampling", "class weight", "threshold", "AUC", "precision-recall", "stratified"],
        model_answer_hint="Techniques: oversampling minority (SMOTE), undersampling majority, class weights in loss function, threshold tuning, ensemble methods (balanced random forest). Evaluation: use AUC-ROC, precision-recall curve instead of accuracy. Stratified sampling in cross-validation. Generate synthetic samples.",
    ),
    Question(
        id="ml_017", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="What is transfer learning and when should you use it?",
        expected_keywords=["transfer learning", "pretrained", "fine-tune", "feature extraction", "domain", "small dataset", "ImageNet", "BERT", "layers"],
        model_answer_hint="Transfer learning uses a model pretrained on large dataset and adapts it to new task. Approaches: feature extraction (freeze layers, train classifier) or fine-tuning (unfreeze some/all layers). Use when: limited data, similar domain. Examples: ImageNet models for vision, BERT for NLP.",
    ),
    Question(
        id="ml_018", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain the attention mechanism and how Transformers use it.",
        expected_keywords=["attention", "query", "key", "value", "self-attention", "multi-head", "positional encoding", "parallel", "context", "scaled dot-product"],
        model_answer_hint="Attention computes weighted sum of Values based on Query-Key similarity: Attention(Q,K,V) = softmax(QK^T/√d)V. Self-attention: Q, K, V from same input (captures dependencies). Multi-head: parallel attention with different projections. Transformers: stacked self-attention + feedforward layers. Positional encoding for sequence order.",
    ),
    Question(
        id="ml_019", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How do you perform hyperparameter tuning effectively?",
        expected_keywords=["grid search", "random search", "Bayesian optimization", "cross-validation", "hyperparameter", "Optuna", "learning curve", "early stopping"],
        model_answer_hint="Methods: Grid search (exhaustive, expensive), Random search (often equally effective, cheaper), Bayesian optimization (Optuna, informed search using prior results). Use cross-validation for evaluation. Learning curves to diagnose. Early stopping to save compute. Start coarse, then fine-tune promising regions.",
    ),
    Question(
        id="ml_020", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="What is dimensionality reduction? Explain PCA and t-SNE.",
        expected_keywords=["PCA", "t-SNE", "dimensionality reduction", "variance", "principal component", "visualization", "curse of dimensionality", "eigenvector", "non-linear"],
        model_answer_hint="Dimensionality reduction projects high-dimensional data to lower dimensions. PCA: linear, preserves maximum variance, uses eigenvectors of covariance matrix, good for feature reduction. t-SNE: non-linear, preserves local neighborhoods, best for 2D/3D visualization (not for feature reduction). PCA is deterministic, t-SNE is stochastic.",
    ),
    Question(
        id="ml_021", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain the difference between batch normalization and layer normalization.",
        expected_keywords=["batch normalization", "layer normalization", "normalize", "training", "inference", "mean", "variance", "activation", "stable"],
        model_answer_hint="Batch norm: normalizes across the batch dimension (per feature). Depends on batch size, uses running stats at inference. Layer norm: normalizes across features for each sample (independent of batch). Layer norm preferred for RNNs/Transformers, batch norm for CNNs. Both stabilize training.",
    ),
    Question(
        id="ml_022", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How do you deploy machine learning models to production?",
        expected_keywords=["deployment", "serving", "API", "containerize", "monitoring", "A/B testing", "latency", "batch vs real-time", "versioning"],
        model_answer_hint="Options: REST API (Flask/FastAPI + Docker), managed services (SageMaker, Vertex AI), edge deployment. Considerations: latency (batch vs real-time), model versioning, A/B testing, monitoring (data drift, performance degradation), containerization for reproducibility, feature store for consistency.",
    ),
    Question(
        id="ml_023", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="What is data leakage and how do you prevent it?",
        expected_keywords=["data leakage", "target leakage", "train-test contamination", "future information", "pipeline", "cross-validation", "preprocessing"],
        model_answer_hint="Data leakage: using information during training that won't be available at prediction time. Types: target leakage (features derived from target), train-test contamination (preprocessing on full data before split). Prevention: pipeline (fit on train only), proper temporal splits, careful feature engineering.",
    ),
    Question(
        id="ml_024", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain word embeddings: Word2Vec, GloVe, and contextual embeddings.",
        expected_keywords=["Word2Vec", "GloVe", "embedding", "vector", "semantic", "context", "CBOW", "skip-gram", "BERT", "contextual"],
        model_answer_hint="Word2Vec: learns word vectors from local context (CBOW predicts word from context, Skip-gram predicts context from word). GloVe: global co-occurrence statistics. Both produce static embeddings (one vector per word). Contextual (BERT, GPT): different vectors based on sentence context—captures polysemy.",
    ),
    Question(
        id="ml_025", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How do you evaluate and compare machine learning models?",
        expected_keywords=["metrics", "cross-validation", "statistical test", "baseline", "learning curve", "confusion matrix", "ROC", "holdout", "significance"],
        model_answer_hint="Use appropriate metrics for task (accuracy, F1, AUC, RMSE). Cross-validation for robust estimates. Statistical tests (paired t-test, Wilcoxon) for significance. Compare against baselines. Learning curves for data sufficiency. Consider computational cost, interpretability, deployment constraints alongside performance.",
    ),
    Question(
        id="ml_026", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="What is model interpretability and what tools help achieve it?",
        expected_keywords=["interpretability", "SHAP", "LIME", "feature importance", "explainability", "partial dependence", "black box", "trust", "regulation"],
        model_answer_hint="Interpretability: understanding why a model makes predictions. Tools: SHAP (Shapley values, consistent feature attribution), LIME (local linear approximations), feature importance (tree-based), partial dependence plots, attention visualization. Important for trust, debugging, regulatory compliance (GDPR right to explanation).",
    ),
    Question(
        id="ml_027", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="Explain the concept of an ensemble model and different ensemble strategies.",
        expected_keywords=["ensemble", "bagging", "boosting", "stacking", "voting", "averaging", "diversity", "meta-learner", "combination"],
        model_answer_hint="Ensembles combine multiple models for better performance. Strategies: Bagging (parallel, reduce variance—Random Forest), Boosting (sequential, reduce bias—XGBoost), Stacking (train meta-learner on base model predictions), Voting/Averaging (simple combination). Key: model diversity. Often wins competitions.",
    ),
    Question(
        id="ml_028", topic="ml_advanced", difficulty="medium", category="machine_learning",
        question_type="technical",
        text="How do you handle missing data in machine learning?",
        expected_keywords=["missing data", "imputation", "mean", "median", "KNN", "MICE", "indicator", "drop", "pattern", "mechanism"],
        model_answer_hint="Methods: deletion (listwise/pairwise—only if MCAR), imputation (mean/median for simple, KNN/MICE for sophisticated), indicator features (add is_missing column), model-based (algorithms that handle NA natively—XGBoost). Understand missing mechanism (MCAR, MAR, MNAR). Never impute target variable.",
    ),
    # --- HARD (12) ---
    Question(
        id="ml_029", topic="ml_deep", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Explain the training dynamics of deep neural networks: vanishing/exploding gradients and solutions.",
        expected_keywords=["vanishing gradient", "exploding gradient", "ReLU", "batch normalization", "residual connection", "initialization", "gradient clipping", "skip connection"],
        model_answer_hint="Vanishing: gradients shrink through layers (sigmoid/tanh). Exploding: gradients grow uncontrollably. Solutions: ReLU activation (non-saturating), batch/layer normalization (stable gradients), residual/skip connections (direct gradient paths), proper initialization (Xavier, He), gradient clipping, LSTM/GRU for sequences.",
    ),
    Question(
        id="ml_030", topic="ml_deep", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do GANs (Generative Adversarial Networks) work and what are their training challenges?",
        expected_keywords=["GAN", "generator", "discriminator", "adversarial", "mode collapse", "training stability", "Nash equilibrium", "Wasserstein", "minimax"],
        model_answer_hint="GANs: generator creates fake samples, discriminator distinguishes real/fake. Minimax game—generator improves until discriminator can't tell difference. Challenges: mode collapse (generator outputs limited variety), training instability, non-convergence. Solutions: Wasserstein GAN, spectral normalization, progressive growing.",
    ),
    Question(
        id="ml_031", topic="ml_deep", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Explain the architecture and training of large language models (LLMs).",
        expected_keywords=["Transformer", "pretraining", "fine-tuning", "RLHF", "tokenization", "attention", "scale", "emergent", "parameter", "context window"],
        model_answer_hint="Architecture: decoder-only Transformer with self-attention. Training: unsupervised pretraining on massive text (next-token prediction), instruction fine-tuning (supervised), RLHF for alignment. Tokenization (BPE/SentencePiece). Scaling laws (more params + data = better). Emergent capabilities at scale. Challenges: hallucination, alignment, cost.",
    ),
    Question(
        id="ml_032", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do you design a recommendation system at scale?",
        expected_keywords=["collaborative filtering", "content-based", "matrix factorization", "embedding", "two-tower", "cold start", "serving", "real-time", "diversity"],
        model_answer_hint="Hybrid approach: candidate generation (approximate nearest neighbors on embeddings) + ranking (deep model with features). Collaborative filtering for user-item interactions, content-based for cold start. Two-tower architecture for efficient retrieval. Considerations: real-time serving, exploration/exploitation, diversity, freshness.",
    ),
    Question(
        id="ml_033", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Explain MLOps: how do you operationalize machine learning at scale?",
        expected_keywords=["MLOps", "pipeline", "versioning", "monitoring", "retraining", "feature store", "registry", "CI/CD", "drift", "reproducibility"],
        model_answer_hint="MLOps lifecycle: feature store (consistent features), experiment tracking (MLflow/W&B), model registry (versioning), automated pipelines (training + evaluation + deployment), CI/CD for ML, monitoring (data drift, concept drift, model degradation), automated retraining triggers, A/B testing framework, reproducibility (code + data + config versioning).",
    ),
    Question(
        id="ml_034", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do you detect and handle concept drift in production models?",
        expected_keywords=["concept drift", "data drift", "monitoring", "detection", "retrain", "statistical test", "window", "distribution", "alert"],
        model_answer_hint="Concept drift: relationship between input and target changes over time. Detection: monitor prediction distribution, feature distributions (KL divergence, KS test, PSI), model performance metrics over time windows. Handle: automatic retraining triggers, sliding window training, ensemble of models from different time periods, gradual model replacement.",
    ),
    Question(
        id="ml_035", topic="ml_deep", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Explain distributed training strategies for deep learning.",
        expected_keywords=["data parallel", "model parallel", "pipeline parallel", "gradient accumulation", "all-reduce", "mixed precision", "DeepSpeed", "FSDP"],
        model_answer_hint="Data parallelism: same model on multiple GPUs, different data, synchronize gradients (all-reduce). Model parallelism: split model layers across GPUs. Pipeline parallelism: split model into stages, micro-batches. Mixed precision (FP16/BF16) for memory/speed. Tools: PyTorch FSDP, DeepSpeed ZeRO. Gradient accumulation for effective larger batches.",
    ),
    Question(
        id="ml_036", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do you build a robust feature store for machine learning?",
        expected_keywords=["feature store", "online", "offline", "consistency", "serving", "materialization", "point-in-time", "registry", "Feast"],
        model_answer_hint="Feature store provides: offline store (batch features for training, point-in-time correct joins), online store (low-latency serving), feature registry (documentation, lineage, sharing), transformation logic. Ensure training-serving consistency. Tools: Feast, Tecton. Handles: feature versioning, backfilling, monitoring, access control.",
    ),
    Question(
        id="ml_037", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Explain federated learning and its privacy benefits.",
        expected_keywords=["federated", "privacy", "decentralized", "gradient", "aggregation", "differential privacy", "communication", "heterogeneous", "on-device"],
        model_answer_hint="Federated learning trains models across decentralized devices without sharing raw data. Process: distribute model, local training, send gradients/updates to server, aggregate (FedAvg). Privacy: data stays on device. Challenges: communication cost, non-IID data, differential privacy for gradient protection, model heterogeneity. Used in mobile (keyboard prediction).",
    ),
    Question(
        id="ml_038", topic="ml_deep", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do you handle catastrophic forgetting in continual/incremental learning?",
        expected_keywords=["catastrophic forgetting", "continual learning", "elastic weight consolidation", "replay", "regularization", "knowledge distillation", "plasticity"],
        model_answer_hint="Catastrophic forgetting: learning new tasks degrades old task performance. Solutions: Elastic Weight Consolidation (penalize changes to important weights), experience replay (store/replay old examples), knowledge distillation (old model as teacher), progressive networks (add capacity), modular architectures. Balance stability vs. plasticity.",
    ),
    Question(
        id="ml_039", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="How do you evaluate and improve the fairness of ML models?",
        expected_keywords=["fairness", "bias", "demographic parity", "equalized odds", "disparate impact", "audit", "protected", "mitigation", "trade-off"],
        model_answer_hint="Fairness metrics: demographic parity (equal positive rate across groups), equalized odds (equal TPR/FPR), individual fairness. Detection: audit predictions across protected attributes. Mitigation: pre-processing (resampling, reweighting), in-processing (constrained optimization, adversarial debiasing), post-processing (threshold adjustment). Fairness often trades off with accuracy.",
    ),
    Question(
        id="ml_040", topic="ml_advanced", difficulty="hard", category="machine_learning",
        question_type="technical",
        text="Design an end-to-end NLP pipeline for production text classification.",
        expected_keywords=["tokenization", "preprocessing", "embedding", "fine-tune", "evaluation", "deployment", "monitoring", "pipeline", "versioning", "serving"],
        model_answer_hint="Pipeline: data collection → cleaning/preprocessing → annotation (with guidelines, IAA) → tokenization → model selection (fine-tune pretrained Transformer or train classical ML baseline) → evaluation (cross-val, error analysis) → deployment (ONNX optimization, batched inference) → monitoring (drift detection, feedback loop). Version everything: data, code, model, config.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM DESIGN QUESTIONS (35)
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_DESIGN_QUESTIONS = [
    # --- EASY (8) ---
    Question(
        id="sd_001", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is horizontal vs vertical scaling and when would you use each?",
        expected_keywords=["horizontal", "vertical", "scale out", "scale up", "load balancer", "stateless", "cost", "limit", "distributed"],
        model_answer_hint="Vertical (scale up): bigger machine (more CPU/RAM). Limit: hardware ceiling, single point of failure. Horizontal (scale out): more machines behind load balancer. Requires stateless design. Horizontal preferred for high availability and cost efficiency at scale.",
    ),
    Question(
        id="sd_002", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is a load balancer and what algorithms does it use?",
        expected_keywords=["load balancer", "round-robin", "least connections", "consistent hashing", "health check", "distribute", "L4", "L7", "sticky session"],
        model_answer_hint="Load balancer distributes traffic across servers. Algorithms: round-robin (equal rotation), least connections (fewest active), weighted (capacity-based), IP hash (sticky sessions), consistent hashing. L4 (transport—TCP) vs L7 (application—HTTP routing). Health checks remove unhealthy backends.",
    ),
    Question(
        id="sd_003", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is caching and what are common caching strategies?",
        expected_keywords=["cache", "TTL", "eviction", "LRU", "cache-aside", "write-through", "write-back", "invalidation", "hit rate", "Redis"],
        model_answer_hint="Caching stores frequently accessed data in fast storage (Redis, Memcached). Strategies: cache-aside (app manages), write-through (write to cache + DB), write-back (write to cache, async to DB). Eviction: LRU, LFU, TTL. Challenges: invalidation, consistency, thundering herd.",
    ),
    Question(
        id="sd_004", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is a CDN and how does it improve performance?",
        expected_keywords=["CDN", "edge", "latency", "cache", "origin", "geographic", "static", "TTL", "content delivery"],
        model_answer_hint="CDN (Content Delivery Network) caches content at geographically distributed edge servers. Reduces latency (serve from nearest location), decreases origin server load, handles traffic spikes. Best for static assets (images, CSS, JS). Configure TTL and cache invalidation rules.",
    ),
    Question(
        id="sd_005", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is a message queue and why use one?",
        expected_keywords=["message queue", "decouple", "async", "producer", "consumer", "buffer", "reliability", "RabbitMQ", "Kafka", "SQS"],
        model_answer_hint="Message queues decouple producers from consumers, enabling asynchronous processing. Benefits: absorb traffic spikes (buffer), reliable delivery (persistence), retry failed processing, scale consumers independently. Examples: RabbitMQ (traditional), Kafka (streaming), SQS (managed). Essential for microservices.",
    ),
    Question(
        id="sd_006", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="Explain the REST architectural style and its constraints.",
        expected_keywords=["REST", "stateless", "resource", "HTTP methods", "URI", "uniform interface", "cacheable", "client-server", "HATEOAS"],
        model_answer_hint="REST: architectural style for APIs. Constraints: client-server separation, stateless (no server-side session), cacheable, uniform interface (resources + HTTP verbs), layered system. Resources identified by URIs. HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE. Status codes for responses.",
    ),
    Question(
        id="sd_007", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is database replication and what are its types?",
        expected_keywords=["replication", "master-slave", "primary-replica", "synchronous", "asynchronous", "read replica", "availability", "consistency", "failover"],
        model_answer_hint="Replication copies data across multiple servers. Primary-replica: one write node, multiple read replicas. Synchronous (consistent but slower) vs asynchronous (faster but lag). Benefits: read scaling, high availability (failover), geographic distribution. Trade-off: consistency vs performance.",
    ),
    Question(
        id="sd_008", topic="system_design_basics", difficulty="easy", category="system_design",
        question_type="technical",
        text="What is the difference between monolithic and microservices architecture?",
        expected_keywords=["monolithic", "microservices", "single", "distributed", "deployment", "scaling", "coupling", "team", "complexity"],
        model_answer_hint="Monolithic: single deployable unit, simpler initially, harder to scale individual parts. Microservices: independent services, own databases, independent deployment, team autonomy. Trade-offs: microservices add distributed system complexity (networking, consistency, debugging) but enable independent scaling and team velocity.",
    ),
    # --- MEDIUM (15) ---
    Question(
        id="sd_009", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a URL shortening service like bit.ly.",
        expected_keywords=["hash", "base62", "database", "redirect", "cache", "collision", "expiration", "analytics", "distributed ID"],
        model_answer_hint="Generate short code: base62 encoding of auto-increment ID or hash with collision handling. Store mapping in DB (key-value or relational). Cache popular URLs in Redis. 301/302 redirect. Analytics: track clicks, referrers. Handle custom URLs, expiration. Scale: distributed ID generation, multiple DB shards by short code.",
    ),
    Question(
        id="sd_010", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a rate limiter. What algorithms would you use?",
        expected_keywords=["rate limiter", "token bucket", "sliding window", "fixed window", "distributed", "Redis", "429", "throttle", "leaky bucket"],
        model_answer_hint="Algorithms: Token Bucket (flexible burst), Leaky Bucket (smooth output), Fixed Window (simple, boundary issues), Sliding Window Log (accurate, memory-heavy), Sliding Window Counter (balance of accuracy and efficiency). Implement with Redis (atomic INCR + EXPIRE). Return 429 with retry-after header. Consider per-user, per-IP, per-API limits.",
    ),
    Question(
        id="sd_011", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a notification system that supports email, SMS, and push notifications.",
        expected_keywords=["queue", "template", "priority", "preference", "retry", "delivery", "rate limit", "batch", "provider", "fallback"],
        model_answer_hint="Architecture: API → validation → message queue (per channel + priority) → workers → providers. Components: template engine, user preferences (opt-in/out per channel), rate limiting, deduplication, delivery tracking, retry with exponential backoff, fallback providers, batch for non-urgent. Separate high-priority queue.",
    ),
    Question(
        id="sd_012", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How would you design a real-time chat application?",
        expected_keywords=["WebSocket", "message queue", "presence", "delivery", "persistence", "group chat", "read receipt", "scaling", "fan-out"],
        model_answer_hint="WebSocket for real-time bidirectional communication. Message flow: sender → server → message queue → recipient's WebSocket connection. Persistence in DB for history. Presence service (online/offline/typing). Read receipts. Group chat: fan-out to all members. Scale: connection servers behind LB, message routing service.",
    ),
    Question(
        id="sd_013", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a distributed cache system.",
        expected_keywords=["consistent hashing", "replication", "eviction", "partition", "availability", "invalidation", "hot key", "cluster", "failover"],
        model_answer_hint="Consistent hashing for key distribution across nodes (minimal redistribution on add/remove). Replication for availability. Eviction policies (LRU/LFU/TTL). Handle hot keys (replication, local caching). Cluster management: health checks, auto-failover, rebalancing. Cache-aside pattern. Consider write policies and consistency guarantees.",
    ),
    Question(
        id="sd_014", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How would you design an autocomplete/typeahead suggestion system?",
        expected_keywords=["trie", "prefix", "ranking", "cache", "precompute", "latency", "personalization", "top-k", "update"],
        model_answer_hint="Data structure: Trie for prefix lookup with top-k results at each node. Precompute popular suggestions, cache heavily (results are highly repetitive). Ranking by frequency/recency/personalization. Async data pipeline to update suggestions. CDN for static popular prefixes. Target <100ms latency.",
    ),
    Question(
        id="sd_015", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a task scheduling system like cron at scale.",
        expected_keywords=["scheduler", "queue", "execution", "retry", "idempotent", "distributed lock", "priority", "dead letter", "monitoring"],
        model_answer_hint="Components: task store (DB), scheduler (checks due tasks), execution queue, workers. Distributed lock to prevent duplicate execution. Idempotent tasks for safe retries. Priority queues. Dead letter queue for failures. Monitoring + alerting on failures/SLA breaches. Handle timezone, recurring schedules, one-time tasks.",
    ),
    Question(
        id="sd_016", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How would you design an API gateway?",
        expected_keywords=["gateway", "routing", "authentication", "rate limiting", "transformation", "aggregation", "circuit breaker", "logging", "versioning"],
        model_answer_hint="API gateway: single entry point for clients. Responsibilities: request routing (path/header-based), authentication/authorization, rate limiting, request/response transformation, request aggregation, protocol translation, circuit breaker, logging/monitoring, API versioning, caching, SSL termination. Consider edge vs service mesh approaches.",
    ),
    Question(
        id="sd_017", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a file storage service like Dropbox.",
        expected_keywords=["chunking", "deduplication", "sync", "versioning", "metadata", "block storage", "conflict resolution", "delta sync", "encryption"],
        model_answer_hint="Architecture: file chunking (4MB blocks), content-addressed storage (deduplication via hash), metadata service (file tree, permissions), sync engine (track local vs remote changes), delta sync (only upload changed chunks), versioning, conflict resolution (last-write-wins or user choice), end-to-end encryption option.",
    ),
    Question(
        id="sd_018", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How would you design a search engine for a large e-commerce site?",
        expected_keywords=["inverted index", "ranking", "relevance", "Elasticsearch", "facets", "typo tolerance", "autocomplete", "personalization", "real-time"],
        model_answer_hint="Inverted index for text search (Elasticsearch/Solr). Ranking: TF-IDF/BM25 + boosting (popularity, freshness, personalization). Features: faceted search (filters), autocomplete, typo tolerance (edit distance), synonyms, search-as-you-type. Real-time indexing for new products. A/B test ranking changes. Track click-through rate for quality.",
    ),
    Question(
        id="sd_019", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a monitoring and alerting system.",
        expected_keywords=["metrics", "time-series", "alerting", "dashboard", "threshold", "anomaly", "aggregation", "retention", "SLO"],
        model_answer_hint="Collect: agents push metrics to time-series DB (Prometheus model) or push gateway. Store: time-series DB with downsampling/retention policies. Alert: threshold-based + anomaly detection, escalation policies, deduplication. Visualize: dashboards with drill-down. Define SLOs, alert on error budget burn rate. Avoid alert fatigue.",
    ),
    Question(
        id="sd_020", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How would you design a payment processing system?",
        expected_keywords=["idempotent", "transaction", "reconciliation", "retry", "ledger", "encryption", "PCI", "webhook", "state machine"],
        model_answer_hint="Idempotency keys for safe retries. State machine for payment lifecycle (pending → authorized → captured → settled). Double-entry ledger for accounting. Encryption + PCI compliance. Webhook notifications. Reconciliation service. Handle timeouts gracefully (check before retry). Dead letter queue for failed callbacks.",
    ),
    Question(
        id="sd_021", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="What are the key principles of designing distributed systems?",
        expected_keywords=["CAP", "consistency", "availability", "partition", "idempotent", "retry", "timeout", "circuit breaker", "eventual consistency"],
        model_answer_hint="Principles: CAP theorem awareness, design for failure, idempotent operations, timeout + retry with backoff, circuit breaker for cascading failure prevention, eventual consistency where acceptable, distributed tracing, health checks, graceful degradation, bulkhead pattern for isolation.",
    ),
    Question(
        id="sd_022", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="Design a content delivery system for streaming video.",
        expected_keywords=["CDN", "encoding", "adaptive bitrate", "HLS", "DASH", "chunk", "edge", "transcoding", "buffer", "latency"],
        model_answer_hint="Upload → transcode to multiple resolutions/bitrates (adaptive streaming). Chunk into small segments (HLS/DASH). Distribute via CDN edge servers. Client player adapts quality based on bandwidth. Architecture: origin storage (S3), transcoding pipeline, CDN, manifest files. Handle live vs VOD differently. DRM for content protection.",
    ),
    Question(
        id="sd_023", topic="system_design", difficulty="medium", category="system_design",
        question_type="technical",
        text="How do you design for idempotency in distributed systems?",
        expected_keywords=["idempotency", "key", "deduplication", "retry", "exactly-once", "token", "state", "side effect", "database"],
        model_answer_hint="Idempotency: repeating operation produces same result. Implementation: idempotency key (client-generated UUID), store request+result mapping, check before processing, return cached result on retry. Database: use unique constraints, conditional updates (IF NOT EXISTS). Message processing: track processed message IDs. Essential for payment/financial systems.",
    ),
    # --- HARD (12) ---
    Question(
        id="sd_024", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design Twitter's home timeline/news feed at scale.",
        expected_keywords=["fan-out", "timeline", "cache", "ranking", "real-time", "pull vs push", "celebrity", "sharding", "pre-compute"],
        model_answer_hint="Hybrid fan-out: fan-out on write for normal users (pre-compute timelines on new tweet), fan-out on read for celebrities (too expensive to push to millions of followers). Timeline stored in Redis (per user). Ranking service for relevance. Shard by user_id. Handle deletes, new follows. Real-time delivery via WebSocket.",
    ),
    Question(
        id="sd_025", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a distributed unique ID generation system.",
        expected_keywords=["Snowflake", "timestamp", "machine ID", "sequence", "ordering", "collision-free", "distributed", "64-bit", "datacenter"],
        model_answer_hint="Twitter Snowflake approach: 64-bit ID = timestamp (41 bits, ~69 years) + datacenter ID (5 bits) + machine ID (5 bits) + sequence (12 bits, 4096/ms/machine). Guaranteed unique, roughly time-ordered, no coordination needed. Alternatives: UUID (128-bit, no ordering), database sequence (bottleneck), ULID (sortable UUID).",
    ),
    Question(
        id="sd_026", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a distributed consensus system (like Raft or Paxos).",
        expected_keywords=["consensus", "Raft", "Paxos", "leader election", "log replication", "majority", "quorum", "split brain", "term", "heartbeat"],
        model_answer_hint="Raft: leader-based consensus. Components: leader election (term-based, majority vote, random timeouts prevent split vote), log replication (leader appends, followers replicate, committed on majority ack), safety (committed entries never lost). Handles: leader failure, network partition, follower catch-up. Simpler than Paxos, same guarantees.",
    ),
    Question(
        id="sd_027", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design Google Maps or a navigation system.",
        expected_keywords=["graph", "shortest path", "Dijkstra", "A*", "tile", "precomputation", "hierarchical", "real-time traffic", "routing", "ETA"],
        model_answer_hint="Road network as weighted graph. Shortest path: hierarchical approach (precompute highway-level routes, detail local segments). A* with landmarks for fast routing. Real-time traffic: speed data from users, update edge weights. Map tiles for rendering (pre-rendered at zoom levels). ETA: ML model on historical + real-time. Turn-by-turn: edge sequence with instructions.",
    ),
    Question(
        id="sd_028", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a distributed rate limiter that works across multiple data centers.",
        expected_keywords=["distributed", "rate limit", "consistency", "Redis cluster", "eventual consistency", "local + global", "sync", "race condition", "token bucket"],
        model_answer_hint="Challenges: global rate limit across regions without latency. Approach: local rate limiter per data center with periodic sync to global store. Accept slight over-limit during sync window. Redis cluster with CRDTs for conflict-free merging. Or: split rate allocation per region (proportional to traffic). Two-tier: local fast path + async global reconciliation.",
    ),
    Question(
        id="sd_029", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a real-time fraud detection system for financial transactions.",
        expected_keywords=["real-time", "ML model", "rules engine", "streaming", "feature store", "latency", "false positive", "alert", "pattern"],
        model_answer_hint="Pipeline: transaction → feature enrichment (real-time from feature store) → rules engine (velocity checks, blacklists) + ML model (anomaly score) → decision (approve/decline/review). Requirements: <100ms latency, handle millions TPS. Stream processing (Kafka + Flink), ML models updated frequently. Balance false positive rate vs. fraud detection. Feedback loop for model improvement.",
    ),
    Question(
        id="sd_030", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a distributed key-value store like DynamoDB.",
        expected_keywords=["consistent hashing", "replication", "vector clock", "quorum", "gossip", "sloppy quorum", "anti-entropy", "partition", "eventually consistent"],
        model_answer_hint="Consistent hashing for partitioning, configurable replication (N replicas). Quorum reads/writes (R + W > N for strong consistency). Vector clocks for conflict detection. Gossip protocol for membership. Sloppy quorum + hinted handoff for availability during failures. Anti-entropy (Merkle trees) for replica synchronization. Tunable consistency (R, W, N).",
    ),
    Question(
        id="sd_031", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a web crawler that indexes billions of pages.",
        expected_keywords=["frontier", "politeness", "deduplication", "priority", "distributed", "robots.txt", "URL normalization", "content hash", "crawl budget"],
        model_answer_hint="Components: URL frontier (priority queue, politeness per domain), fetcher (distributed workers respecting robots.txt, rate limits), content processor (extract text, links, dedup by content hash), URL normalizer (canonicalize), storage (content store + metadata). Prioritize by PageRank/freshness. Bloom filter for seen URLs. Handle traps (infinite calendars).",
    ),
    Question(
        id="sd_032", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design an event sourcing system with CQRS.",
        expected_keywords=["event sourcing", "CQRS", "event store", "projection", "replay", "snapshot", "command", "query", "separation", "eventual consistency"],
        model_answer_hint="Event sourcing: store state changes as immutable events (not current state). CQRS: separate Command (write) and Query (read) models. Event store: append-only log. Read models: projections built from events (optimized for queries). Snapshots for performance (avoid replaying all events). Benefits: audit trail, temporal queries, replay for bug fixes. Challenges: eventual consistency between write/read, schema evolution.",
    ),
    Question(
        id="sd_033", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a global configuration and feature flag management system.",
        expected_keywords=["feature flag", "configuration", "rollout", "segment", "propagation", "consistency", "SDK", "audit", "kill switch"],
        model_answer_hint="Architecture: central management service (CRUD, rules, segments, percentage rollouts), propagation (push via SSE/WebSocket or poll with long-poll), client SDKs (local cache with fallback defaults). Features: gradual rollout (percentage, user segments), kill switch (instant disable), A/B testing integration, audit trail, change approval workflow. Consider: propagation latency, availability (cache if server down).",
    ),
    Question(
        id="sd_034", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design a distributed tracing system like Jaeger/Zipkin.",
        expected_keywords=["trace", "span", "context propagation", "sampling", "correlation ID", "DAG", "latency", "storage", "visualization"],
        model_answer_hint="Each request generates a trace ID, propagated through all services (headers). Each service creates spans (start/end time, metadata, parent span ID). Spans form a DAG representing request flow. Sampling strategy (head-based or tail-based) to control volume. Storage: time-series optimized. Query: by trace ID, service, latency percentile. Visualization: waterfall diagrams.",
    ),
    Question(
        id="sd_035", topic="system_design", difficulty="hard", category="system_design",
        question_type="technical",
        text="Design an online collaborative editing system like Google Docs.",
        expected_keywords=["CRDT", "OT", "operational transformation", "conflict resolution", "real-time", "cursor", "history", "WebSocket", "eventual consistency"],
        model_answer_hint="Approaches: Operational Transformation (transform concurrent operations relative to each other—Google Docs) or CRDTs (conflict-free replicated data types—mathematically guaranteed convergence). Real-time sync via WebSocket. Challenges: cursor management, undo/redo with concurrent edits, offline support, version history. OT requires central server; CRDTs allow P2P.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES & ALGORITHMS QUESTIONS (30)
# ═══════════════════════════════════════════════════════════════════════════════

DSA_QUESTIONS = [
    # --- EASY (8) ---
    Question(
        id="dsa_001", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="What is the difference between an array and a linked list?",
        expected_keywords=["array", "linked list", "contiguous", "pointer", "access", "insertion", "O(1)", "O(n)", "memory", "index"],
        model_answer_hint="Array: contiguous memory, O(1) random access, O(n) insertion/deletion (shifting). Linked list: scattered nodes with pointers, O(n) access, O(1) insertion/deletion at known position. Array: better cache performance. Linked list: dynamic size, no waste.",
    ),
    Question(
        id="dsa_002", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="Explain a hash table and how collisions are handled.",
        expected_keywords=["hash table", "hash function", "collision", "chaining", "open addressing", "O(1)", "bucket", "load factor", "resize"],
        model_answer_hint="Hash table maps keys to indices via hash function. O(1) average lookup/insert. Collision handling: chaining (linked lists at each bucket) or open addressing (probe for next slot—linear, quadratic, double hashing). Resize (rehash) when load factor exceeds threshold.",
    ),
    Question(
        id="dsa_003", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="What is Big O notation and why is it important?",
        expected_keywords=["Big O", "complexity", "time", "space", "worst case", "growth rate", "scalability", "asymptotic", "comparison"],
        model_answer_hint="Big O describes the upper bound of algorithm growth rate as input size increases. Ignores constants and lower-order terms. Common: O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ). Important for comparing algorithm scalability and making informed engineering decisions.",
    ),
    Question(
        id="dsa_004", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="Explain the difference between a stack and a queue.",
        expected_keywords=["stack", "queue", "LIFO", "FIFO", "push", "pop", "enqueue", "dequeue", "last in first out", "first in first out"],
        model_answer_hint="Stack: LIFO (Last In, First Out)—push/pop from top. Like a stack of plates. Uses: undo, recursion, DFS. Queue: FIFO (First In, First Out)—enqueue at back, dequeue from front. Like a line. Uses: BFS, task scheduling, buffering.",
    ),
    Question(
        id="dsa_005", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="What is a binary search tree and its time complexities?",
        expected_keywords=["BST", "binary search tree", "left", "right", "O(log n)", "O(n)", "balanced", "ordered", "search", "insert"],
        model_answer_hint="BST: left child < parent < right child. Operations: O(log n) average for search/insert/delete if balanced, O(n) worst case (degenerate/skewed tree). Balanced variants (AVL, Red-Black) guarantee O(log n). In-order traversal gives sorted sequence.",
    ),
    Question(
        id="dsa_006", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="Explain BFS and DFS traversal algorithms.",
        expected_keywords=["BFS", "DFS", "breadth-first", "depth-first", "queue", "stack", "level", "recursion", "visited", "graph"],
        model_answer_hint="BFS: explore level-by-level using a queue. Finds shortest path in unweighted graphs. DFS: explore as deep as possible using stack/recursion. Better for cycle detection, topological sort. Both visit all reachable nodes. Time: O(V+E) for both in graphs.",
    ),
    Question(
        id="dsa_007", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="What is binary search and when can you apply it?",
        expected_keywords=["binary search", "sorted", "divide", "O(log n)", "middle", "half", "comparison", "monotonic", "condition"],
        model_answer_hint="Binary search: repeatedly divide sorted array in half, compare middle element. O(log n) time. Requires sorted/monotonic data. Application: sorted arrays, finding boundaries, search space reduction. Can generalize to any monotonic function (binary search on answer).",
    ),
    Question(
        id="dsa_008", topic="dsa_basics", difficulty="easy", category="data_structures",
        question_type="technical",
        text="Compare common sorting algorithms and their complexities.",
        expected_keywords=["sorting", "merge sort", "quick sort", "O(n log n)", "stable", "in-place", "comparison", "bubble sort", "time complexity"],
        model_answer_hint="Merge sort: O(n log n) always, stable, not in-place. Quick sort: O(n log n) average, O(n²) worst, in-place, not stable. Heap sort: O(n log n) always, in-place, not stable. Counting/Radix sort: O(n) for integers with limited range. Python uses Timsort (hybrid merge + insertion).",
    ),
    # --- MEDIUM (12) ---
    Question(
        id="dsa_009", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain dynamic programming. What are the two main approaches?",
        expected_keywords=["dynamic programming", "overlapping subproblems", "optimal substructure", "memoization", "tabulation", "top-down", "bottom-up", "cache"],
        model_answer_hint="DP solves problems with overlapping subproblems and optimal substructure. Top-down (memoization): recursive with caching. Bottom-up (tabulation): iterative, fill table from base cases. Steps: define state, recurrence relation, base case, compute order. Classic examples: Fibonacci, knapsack, LCS.",
    ),
    Question(
        id="dsa_010", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="How does a heap (priority queue) work? Explain insert and extract operations.",
        expected_keywords=["heap", "priority queue", "min-heap", "max-heap", "heapify", "sift up", "sift down", "O(log n)", "complete binary tree"],
        model_answer_hint="Heap: complete binary tree where parent ≤ children (min-heap) or ≥ (max-heap). Stored as array (parent i → children 2i+1, 2i+2). Insert: add at end, sift up O(log n). Extract min/max: swap root with last, sift down O(log n). Build heap: O(n). Used in priority queues, heap sort, top-K problems.",
    ),
    Question(
        id="dsa_011", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain graph representations and when to use each.",
        expected_keywords=["adjacency matrix", "adjacency list", "edge list", "dense", "sparse", "space", "time", "weighted", "directed"],
        model_answer_hint="Adjacency matrix: O(V²) space, O(1) edge check, best for dense graphs. Adjacency list: O(V+E) space, O(degree) edge check, best for sparse graphs. Edge list: O(E) space, simple but slow lookups. Most real-world graphs are sparse → adjacency list preferred. Consider weighted edges, directed vs undirected.",
    ),
    Question(
        id="dsa_012", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain Dijkstra's algorithm and its limitations.",
        expected_keywords=["Dijkstra", "shortest path", "greedy", "priority queue", "non-negative", "relaxation", "O(V log V + E)", "weighted", "visited"],
        model_answer_hint="Dijkstra finds shortest paths from source to all nodes in weighted graph. Uses priority queue (min-heap), greedily processes nearest unvisited node, relaxes edges. Complexity: O((V+E) log V) with binary heap. Limitation: doesn't work with negative edge weights (use Bellman-Ford instead).",
    ),
    Question(
        id="dsa_013", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="What is a trie and what are its applications?",
        expected_keywords=["trie", "prefix tree", "character", "node", "autocomplete", "prefix search", "word", "O(m)", "dictionary"],
        model_answer_hint="Trie (prefix tree): tree where each edge represents a character. Paths from root form prefixes. O(m) lookup where m is key length (independent of n). Applications: autocomplete, spell checking, IP routing (longest prefix match), word games. Space: can be large (optimize with compressed trie).",
    ),
    Question(
        id="dsa_014", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain the two-pointer and sliding window techniques.",
        expected_keywords=["two pointer", "sliding window", "linear", "O(n)", "shrink", "expand", "sorted", "substring", "sum"],
        model_answer_hint="Two pointers: two indices moving through array (same direction or converging). For sorted arrays: find pair sum, remove duplicates. Sliding window: maintain a window [left, right] expanding right and shrinking left. For substring/subarray problems with constraints (max sum, unique chars). Both achieve O(n) from O(n²).",
    ),
    Question(
        id="dsa_015", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="How do you detect a cycle in a linked list or graph?",
        expected_keywords=["cycle", "Floyd", "tortoise", "hare", "fast", "slow", "visited", "DFS", "coloring", "O(1) space"],
        model_answer_hint="Linked list: Floyd's tortoise and hare (slow moves 1, fast moves 2—if they meet, cycle exists). O(n) time, O(1) space. Graph: DFS with coloring (white/gray/black): gray node reached again = cycle. Or use visited set. For undirected: parent tracking during DFS.",
    ),
    Question(
        id="dsa_016", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="What is topological sorting and where is it used?",
        expected_keywords=["topological sort", "DAG", "directed acyclic", "dependency", "ordering", "DFS", "Kahn", "in-degree", "prerequisite"],
        model_answer_hint="Topological sort: linear ordering of vertices in DAG such that for every edge u→v, u comes before v. Algorithms: DFS-based (reverse post-order) or Kahn's (BFS with in-degree). Applications: task scheduling, build systems, course prerequisites. Only possible for DAGs (detect cycle if impossible).",
    ),
    Question(
        id="dsa_017", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain the concept of amortized analysis with examples.",
        expected_keywords=["amortized", "average", "worst case", "dynamic array", "resize", "O(1) amortized", "accounting", "potential", "aggregate"],
        model_answer_hint="Amortized analysis: average cost per operation over a sequence of operations. Dynamic array append: usually O(1), occasionally O(n) for resize, but amortized O(1) because resizes double capacity. Methods: aggregate (total cost / operations), accounting (charge extra on cheap ops), potential function.",
    ),
    Question(
        id="dsa_018", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="How would you design an LRU cache?",
        expected_keywords=["LRU", "hash map", "doubly linked list", "O(1)", "eviction", "capacity", "get", "put", "recent"],
        model_answer_hint="LRU Cache: HashMap (key → node) + Doubly Linked List (order by recency). get(): O(1) lookup in map, move node to front. put(): O(1) insert at front, evict from back if full. Both operations O(1). Use OrderedDict in Python for simpler implementation.",
    ),
    Question(
        id="dsa_019", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="Explain backtracking and give examples of problems it solves.",
        expected_keywords=["backtracking", "recursion", "constraint", "prune", "explore", "undo", "decision tree", "N-Queens", "permutations"],
        model_answer_hint="Backtracking: explore solution space by making choices, backtrack (undo) when constraints are violated. Pruning eliminates branches early. Pattern: choose → explore → unchoose. Examples: N-Queens, Sudoku solver, permutations/combinations, word search. Time can be exponential but pruning helps in practice.",
    ),
    Question(
        id="dsa_020", topic="dsa_advanced", difficulty="medium", category="data_structures",
        question_type="technical",
        text="What is a balanced BST and how do AVL trees maintain balance?",
        expected_keywords=["AVL", "balanced", "rotation", "height", "balance factor", "left rotation", "right rotation", "O(log n)", "self-balancing"],
        model_answer_hint="AVL tree: self-balancing BST where height difference between left and right subtrees (balance factor) is at most 1. After insert/delete, perform rotations (left, right, left-right, right-left) to restore balance. Guarantees O(log n) for all operations. Stricter balance than Red-Black trees.",
    ),
    # --- HARD (10) ---
    Question(
        id="dsa_021", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="Explain the Aho-Corasick algorithm for multi-pattern string matching.",
        expected_keywords=["Aho-Corasick", "trie", "failure link", "multi-pattern", "automaton", "linear", "string matching", "suffix", "BFS"],
        model_answer_hint="Aho-Corasick builds an automaton from a trie of patterns with failure links (like KMP's failure function but for trie). Process text in one pass: follow trie edges for matches, follow failure links on mismatch. O(n + m + z) where n=text, m=total pattern length, z=matches. Used in antivirus scanning, network intrusion detection.",
    ),
    Question(
        id="dsa_022", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="How do B-trees and B+ trees work? Why are they used in databases?",
        expected_keywords=["B-tree", "B+ tree", "disk", "branching factor", "balanced", "range query", "leaf", "node", "page", "I/O"],
        model_answer_hint="B-trees: balanced multi-way trees with high branching factor, minimizing tree height → fewer disk I/O. B+ trees: all data in leaves (linked), internal nodes only keys (more keys per node). B+ trees better for range queries (leaf scan). Databases use them because each node = disk page, minimizing random I/O.",
    ),
    Question(
        id="dsa_023", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="Explain the concept of a Bloom filter and its applications.",
        expected_keywords=["Bloom filter", "probabilistic", "false positive", "no false negative", "hash", "bit array", "space efficient", "membership"],
        model_answer_hint="Bloom filter: space-efficient probabilistic membership test. k hash functions map elements to positions in bit array. Query: if all k positions set → probably in set (possible false positive). If any position 0 → definitely not in set (no false negative). Applications: cache lookup (avoid disk), spell check, network routing.",
    ),
    Question(
        id="dsa_024", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="What is a segment tree and when would you use one?",
        expected_keywords=["segment tree", "range query", "update", "O(log n)", "interval", "lazy propagation", "build", "merge", "leaf"],
        model_answer_hint="Segment tree: supports range queries (sum, min, max, GCD) and point/range updates in O(log n). Built recursively: each node stores aggregate of its range. Lazy propagation defers range updates for O(log n) range updates. Use for: range sum queries with updates, interval problems, competitive programming.",
    ),
    Question(
        id="dsa_025", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="Explain the Union-Find (Disjoint Set Union) data structure.",
        expected_keywords=["Union-Find", "disjoint set", "find", "union", "path compression", "rank", "connected components", "cycle", "Kruskal"],
        model_answer_hint="Union-Find: maintains disjoint sets with two operations. Find: determine which set an element belongs to (with path compression for O(α(n)) amortized). Union: merge two sets (by rank/size for balance). Applications: Kruskal's MST, connected components, cycle detection in undirected graphs. Near-constant amortized operations.",
    ),
    Question(
        id="dsa_026", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="How would you solve the traveling salesman problem approximately?",
        expected_keywords=["TSP", "NP-hard", "heuristic", "approximation", "greedy", "2-opt", "dynamic programming", "Christofides", "nearest neighbor"],
        model_answer_hint="TSP is NP-hard (exact: O(2ⁿ·n) DP with bitmask). Approximations: nearest neighbor heuristic, 2-opt/3-opt local improvement, Christofides algorithm (1.5x optimal guarantee for metric TSP), genetic algorithms, simulated annealing. For small n (≤20): bitmask DP. For large: combine construction heuristic + local search.",
    ),
    Question(
        id="dsa_027", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="Explain consistent hashing and its use in distributed systems.",
        expected_keywords=["consistent hashing", "ring", "virtual node", "redistribution", "minimal", "node failure", "load balance", "partition"],
        model_answer_hint="Consistent hashing: map keys and servers to a ring (hash space). Key belongs to next server clockwise. Adding/removing server only redistributes keys from adjacent segment (~1/n of keys). Virtual nodes: each server gets multiple positions for better load distribution. Used in: CDN routing, distributed caches, database sharding.",
    ),
    Question(
        id="dsa_028", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="How do you solve problems using the divide and conquer paradigm? Give non-trivial examples.",
        expected_keywords=["divide and conquer", "subproblem", "merge", "recurrence", "Master theorem", "closest pair", "Strassen", "inversions"],
        model_answer_hint="Divide and conquer: split into smaller subproblems, solve recursively, merge solutions. Beyond sorting: closest pair of points (O(n log n)), count inversions (modified merge sort), Strassen's matrix multiplication (O(n^2.81)), Karatsuba multiplication, convex hull. Analyze with Master theorem or recursion tree.",
    ),
    Question(
        id="dsa_029", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="Explain skip lists and how they achieve O(log n) expected search time.",
        expected_keywords=["skip list", "probabilistic", "level", "express lane", "O(log n)", "linked list", "randomized", "balanced", "insert"],
        model_answer_hint="Skip list: layered linked lists where higher levels skip over elements (like express lanes). Each element promoted to higher level with probability 1/2. Expected O(log n) search (traverse top levels first, drop down). Simpler to implement than balanced BSTs with similar performance. Randomized balance without rotations.",
    ),
    Question(
        id="dsa_030", topic="dsa_hard", difficulty="hard", category="data_structures",
        question_type="technical",
        text="How do you efficiently find the k-th smallest element in an unsorted array?",
        expected_keywords=["quickselect", "median of medians", "partition", "O(n)", "pivot", "expected", "worst case", "order statistics"],
        model_answer_hint="Quickselect: partition around pivot (like quicksort), recurse only into relevant half. Expected O(n), worst O(n²). Median-of-medians: deterministic O(n) worst case by choosing good pivot (median of groups of 5). In practice, randomized quickselect is faster due to lower constants. Can also use min-heap of size k: O(n log k).",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# API DESIGN QUESTIONS (20)
# ═══════════════════════════════════════════════════════════════════════════════

API_QUESTIONS = [
    Question(
        id="api_001", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What makes a good REST API? What are best practices?",
        expected_keywords=["resource", "naming", "HTTP methods", "status codes", "versioning", "consistent", "documentation", "pagination", "HATEOAS"],
        model_answer_hint="Best practices: resource-based URLs (nouns, not verbs), proper HTTP methods, meaningful status codes, consistent naming (plural nouns), pagination for lists, versioning (URL or header), filtering/sorting, error format, documentation (OpenAPI), HATEOAS for discoverability.",
    ),
    Question(
        id="api_002", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What are HTTP status codes and which ones are most important?",
        expected_keywords=["200", "201", "400", "401", "403", "404", "500", "status code", "2xx", "4xx", "5xx"],
        model_answer_hint="2xx success: 200 OK, 201 Created, 204 No Content. 3xx redirect: 301 Permanent, 304 Not Modified. 4xx client error: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests. 5xx server error: 500 Internal, 502 Bad Gateway, 503 Service Unavailable.",
    ),
    Question(
        id="api_003", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What is the difference between REST and GraphQL?",
        expected_keywords=["REST", "GraphQL", "endpoint", "query", "over-fetching", "under-fetching", "schema", "flexibility", "type system"],
        model_answer_hint="REST: multiple endpoints, server defines response shape, over/under-fetching common. GraphQL: single endpoint, client specifies exact data needed (no over-fetching), strongly typed schema, introspection. GraphQL better for complex UIs with varied data needs. REST simpler for CRUD operations and caching.",
    ),
    Question(
        id="api_004", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="How do you handle API authentication and authorization?",
        expected_keywords=["JWT", "OAuth2", "API key", "token", "bearer", "refresh", "stateless", "scope", "RBAC"],
        model_answer_hint="Authentication (who are you): API keys (simple), JWT (stateless, self-contained), OAuth2 (delegated access, third-party). Authorization (what can you do): RBAC, scopes, policies. Best practices: HTTPS always, token expiration, refresh tokens, secure storage, rate limiting per key.",
    ),
    Question(
        id="api_005", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you design API versioning and handle breaking changes?",
        expected_keywords=["versioning", "URL path", "header", "backward compatible", "deprecation", "migration", "breaking change", "semantic"],
        model_answer_hint="Versioning strategies: URL path (/v1/, /v2/), header (Accept: application/vnd.api+v2), query param. Prefer backward-compatible changes (additive). For breaking changes: deprecation warnings, sunset headers, migration guides, support overlap period. Version your API contract, not implementation.",
    ),
    Question(
        id="api_006", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you design APIs for pagination, filtering, and sorting?",
        expected_keywords=["pagination", "cursor", "offset", "filter", "sort", "query parameter", "next", "limit", "total"],
        model_answer_hint="Pagination: offset-based (?page=2&limit=20) or cursor-based (?after=cursor). Cursor preferred for large datasets (consistent, performant). Filtering: field-based query params (?status=active&type=premium). Sorting: ?sort=created_at,-name. Include total count and next/prev links in response.",
    ),
    Question(
        id="api_007", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="What are webhooks and how do you design a reliable webhook system?",
        expected_keywords=["webhook", "callback", "event", "retry", "signature", "idempotent", "delivery", "timeout", "verification"],
        model_answer_hint="Webhooks: server-to-server HTTP callbacks on events. Reliability: retry with exponential backoff (3-5 attempts), signature verification (HMAC), idempotency key in payload, delivery logs, configurable endpoints, timeout handling (5-30s), dead letter queue for persistent failures. Require HTTPS, allow endpoint verification.",
    ),
    Question(
        id="api_008", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you handle errors in API design?",
        expected_keywords=["error", "format", "status code", "message", "code", "details", "consistent", "actionable", "validation"],
        model_answer_hint="Consistent error format: {error: {code: 'VALIDATION_ERROR', message: 'human readable', details: [{field, issue}]}}. Use appropriate HTTP status codes. Provide actionable messages. Include request ID for debugging. Don't expose internal errors. Separate validation errors (field-level) from business logic errors.",
    ),
    Question(
        id="api_009", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="Compare REST, GraphQL, and gRPC for different use cases.",
        expected_keywords=["REST", "GraphQL", "gRPC", "protobuf", "HTTP/2", "streaming", "microservices", "internal", "external", "performance"],
        model_answer_hint="REST: simple CRUD, external APIs, caching-friendly. GraphQL: complex client data needs, frontend-driven development, mobile (reduce round-trips). gRPC: internal microservice communication (protobuf efficiency, HTTP/2 streaming, strong typing, bidirectional). Can combine: gRPC internal + REST/GraphQL external.",
    ),
    Question(
        id="api_010", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you design an API for bulk operations?",
        expected_keywords=["bulk", "batch", "asynchronous", "partial failure", "idempotent", "progress", "limit", "transaction", "status"],
        model_answer_hint="Options: synchronous batch (POST /items/batch with array, return partial results), async job (POST → 202 with job ID, poll for status). Handle partial failures (some succeed, some fail—return per-item status). Set size limits. Make operations idempotent. Consider all-or-nothing vs. partial semantics.",
    ),
    Question(
        id="api_011", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="What is CORS and how do you configure it properly?",
        expected_keywords=["CORS", "cross-origin", "preflight", "OPTIONS", "Access-Control", "Allow-Origin", "credentials", "headers", "browser"],
        model_answer_hint="CORS: browser security mechanism for cross-origin requests. Server specifies allowed origins, methods, headers via Access-Control-* headers. Preflight (OPTIONS) for non-simple requests. Configuration: whitelist specific origins (not *), allow needed methods/headers, handle credentials. Don't disable CORS blindly.",
    ),
    Question(
        id="api_012", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design an API for real-time data with multiple consumer patterns?",
        expected_keywords=["WebSocket", "SSE", "polling", "event stream", "subscription", "backpressure", "reconnection", "multiplexing"],
        model_answer_hint="Options: WebSocket (bidirectional, stateful), Server-Sent Events (server → client, simpler), long-polling (fallback). Consider: subscription management, backpressure handling, reconnection with state sync, multiplexing channels over single connection, authentication for persistent connections, graceful degradation.",
    ),
    Question(
        id="api_013", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design a public API platform with developer experience in mind?",
        expected_keywords=["documentation", "SDK", "sandbox", "rate limiting", "onboarding", "versioning", "playground", "changelog", "support"],
        model_answer_hint="DX considerations: interactive documentation (Swagger UI), SDKs for popular languages, sandbox/test environment, clear onboarding (quick start guide), API playground, consistent error messages, changelog/migration guides, usage dashboard, generous free tier, responsive developer support, webhooks for integration.",
    ),
    Question(
        id="api_014", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design APIs for eventual consistency with optimistic concurrency?",
        expected_keywords=["ETag", "If-Match", "optimistic", "concurrency", "conflict", "retry", "version", "409", "eventual consistency"],
        model_answer_hint="Optimistic concurrency: include version/ETag in responses, require If-Match header on updates. On conflict (version mismatch): return 409 Conflict with current state. Client merges or retries. For eventual consistency: document SLA, provide consistency tokens, offer strong read option (read-your-writes). Design for conflict resolution.",
    ),
    Question(
        id="api_015", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design a multi-tenant API with proper isolation and resource management?",
        expected_keywords=["multi-tenant", "isolation", "rate limit", "quota", "tenant", "API key", "resource limit", "noisy neighbor", "fair usage"],
        model_answer_hint="Tenant identification (API key/JWT with tenant ID). Per-tenant rate limits and quotas. Resource isolation (prevent noisy neighbor). Fair usage policies with burst allowance. Tenant-aware logging and monitoring. Usage metering for billing. Tenant-scoped data access (RLS). Different tiers with different limits.",
    ),
    Question(
        id="api_016", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What is idempotency in APIs and why is it important?",
        expected_keywords=["idempotent", "safe", "retry", "side effect", "key", "POST", "PUT", "GET", "multiple times"],
        model_answer_hint="Idempotent: same request produces same result regardless of how many times executed. GET, PUT, DELETE are naturally idempotent. POST is not. Make POST idempotent with idempotency keys (client-generated UUID in header). Important for: network retries, failure recovery, distributed systems.",
    ),
    Question(
        id="api_017", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you document APIs effectively?",
        expected_keywords=["OpenAPI", "Swagger", "documentation", "example", "description", "schema", "interactive", "auto-generate", "Postman"],
        model_answer_hint="Use OpenAPI/Swagger for machine-readable specs. Include: descriptions, request/response examples, error formats, authentication docs, getting started guide. Interactive docs (Swagger UI, Redoc). Auto-generate from code annotations. Provide Postman collections. Keep docs versioned and up-to-date with CI checks.",
    ),
    Question(
        id="api_018", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="What is API Gateway pattern and what problems does it solve?",
        expected_keywords=["API Gateway", "routing", "aggregation", "authentication", "rate limiting", "transformation", "backend for frontend", "single entry"],
        model_answer_hint="API Gateway: single entry point for clients. Solves: authentication centralization, rate limiting, request routing, protocol translation, response aggregation (reduce client round-trips), request/response transformation, BFF pattern (different gateways for web/mobile). Simplifies clients, adds flexibility for backend refactoring.",
    ),
    Question(
        id="api_019", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design APIs for backward-compatible evolution?",
        expected_keywords=["additive", "optional", "deprecation", "extension", "breaking", "consumer-driven", "contract testing", "nullable"],
        model_answer_hint="Rules for non-breaking changes: only add optional fields, never remove/rename fields, new endpoints are safe, relax validation (accept more), tighten response (return more). Use deprecation headers. Consumer-driven contract tests to catch breaks. Nullable fields over required. Extension points in response format.",
    ),
    Question(
        id="api_020", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design a GraphQL schema for a complex domain?",
        expected_keywords=["schema", "type", "resolver", "N+1", "DataLoader", "mutation", "subscription", "federation", "relay", "pagination"],
        model_answer_hint="Design: domain-driven types (not database tables), connection pattern for pagination (Relay spec), input types for mutations, clear naming conventions. Performance: DataLoader for N+1 (batching), query complexity limits, persisted queries. Architecture: schema federation for microservices (Apollo Federation), schema stitching. Subscriptions for real-time.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# GIT QUESTIONS (15)
# ═══════════════════════════════════════════════════════════════════════════════

GIT_QUESTIONS = [
    Question(
        id="git_001", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is the difference between git merge and git rebase?",
        expected_keywords=["merge", "rebase", "commit history", "linear", "branch", "conflict", "fast-forward", "merge commit", "clean history"],
        model_answer_hint="Merge: creates a merge commit joining two branches (preserves complete history). Rebase: replays commits on top of another branch (creates linear history). Rebase produces cleaner log but rewrites history—never rebase shared/public branches. Merge is safer for collaboration.",
    ),
    Question(
        id="git_002", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is a Git branch and how does branching work?",
        expected_keywords=["branch", "pointer", "commit", "HEAD", "create", "switch", "checkout", "lightweight", "parallel"],
        model_answer_hint="A branch is a lightweight pointer to a commit. Creating a branch just creates a new pointer. HEAD points to current branch. Branches enable parallel development—isolate features, then merge back. Git branching is cheap (40-byte file). Common: feature branches, release branches.",
    ),
    Question(
        id="git_003", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="Explain Git's three main areas: working directory, staging area, and repository.",
        expected_keywords=["working directory", "staging", "index", "repository", "add", "commit", "tracked", "untracked", "history"],
        model_answer_hint="Working directory: current file state. Staging area (index): snapshot of what will go in next commit (git add). Repository (.git): full commit history. Workflow: modify files → stage (git add) → commit (git commit). This separation gives fine-grained control over what gets committed.",
    ),
    Question(
        id="git_004", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you resolve merge conflicts in Git?",
        expected_keywords=["conflict", "merge", "resolve", "markers", "<<<<", "manual", "tool", "accept", "theirs", "ours"],
        model_answer_hint="Conflicts occur when same lines changed in both branches. Git marks conflicts with <<<<<<<, =======, >>>>>>>. Resolution: manually edit file choosing correct content, or use merge tool. Strategies: accept theirs/ours, manual merge, abort. After resolving: git add → git commit. Prevention: small frequent merges, communication.",
    ),
    Question(
        id="git_005", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What is Git Flow and how does it compare to trunk-based development?",
        expected_keywords=["Git Flow", "trunk-based", "feature branch", "develop", "release", "hotfix", "main", "short-lived", "CI/CD"],
        model_answer_hint="Git Flow: long-lived branches (main, develop, feature, release, hotfix). Structured but complex, suited for versioned releases. Trunk-based: short-lived feature branches (hours/1-2 days), merge to main frequently, feature flags for incomplete work. Trunk-based better for CI/CD, faster feedback, less merge pain.",
    ),
    Question(
        id="git_006", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="Explain git cherry-pick and when to use it.",
        expected_keywords=["cherry-pick", "commit", "apply", "specific", "branch", "SHA", "hotfix", "backport", "selective"],
        model_answer_hint="Cherry-pick applies a specific commit from one branch to another (creates new commit with same changes). Use for: hotfix backports (apply fix to release branch), selectively moving features, recovering work from abandoned branches. Creates new commit (different SHA)—not same as merge.",
    ),
    Question(
        id="git_007", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What is git stash and how do you use it effectively?",
        expected_keywords=["stash", "save", "pop", "apply", "temporary", "work in progress", "branch switch", "list", "drop"],
        model_answer_hint="git stash temporarily saves uncommitted changes (working directory + index). Use when switching branches with uncommitted work. Commands: stash push (save), stash pop (restore + remove), stash apply (restore + keep), stash list (show all), stash drop (remove). Can include untracked files with -u.",
    ),
    Question(
        id="git_008", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How does git bisect help find bugs?",
        expected_keywords=["bisect", "binary search", "bug", "good", "bad", "commit", "automated", "regression", "history"],
        model_answer_hint="git bisect performs binary search through commit history to find the commit that introduced a bug. Mark known-good and known-bad commits, git bisect checks out the midpoint for testing. O(log n) commits to check. Can be automated with 'git bisect run <test-script>'. Great for finding regressions.",
    ),
    Question(
        id="git_009", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What are Git hooks and how can they improve workflow?",
        expected_keywords=["hook", "pre-commit", "pre-push", "automation", "lint", "test", "format", "commit-msg", "server-side", "client-side"],
        model_answer_hint="Git hooks: scripts triggered by Git events. Client-side: pre-commit (lint, format), commit-msg (validate message format), pre-push (run tests). Server-side: pre-receive (enforce policies). Use husky + lint-staged for easy setup. Enforce code quality automatically before commits reach remote.",
    ),
    Question(
        id="git_010", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How does Git store data internally? Explain objects, trees, and commits.",
        expected_keywords=["blob", "tree", "commit", "SHA-1", "object", "content-addressable", "DAG", "pack file", "refs"],
        model_answer_hint="Git is a content-addressable filesystem. Object types: blob (file content), tree (directory—points to blobs/trees), commit (points to tree + parent commits + metadata). All identified by SHA-1 hash. Commits form a DAG. Refs (branches/tags) are named pointers to commits. Pack files compress objects for storage.",
    ),
    Question(
        id="git_011", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How do you recover from common Git disasters (force push, lost commits)?",
        expected_keywords=["reflog", "reset", "force push", "recover", "dangling", "ORIG_HEAD", "fsck", "garbage collection", "30 days"],
        model_answer_hint="git reflog: shows all HEAD movements (safety net). Recover force-pushed branch: reflog → reset --hard to previous state. Lost commits: reflog or git fsck --lost-found for dangling commits. Unreachable objects kept ~30 days before GC. ORIG_HEAD saved before dangerous operations. git cherry-pick to rescue specific commits.",
    ),
    Question(
        id="git_012", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What is interactive rebase and how do you use it?",
        expected_keywords=["interactive", "rebase -i", "squash", "fixup", "reword", "reorder", "edit", "history", "clean up"],
        model_answer_hint="git rebase -i: rewrite commit history interactively. Operations: pick (keep), squash/fixup (combine with previous), reword (change message), edit (amend), drop (remove), reorder. Use to clean up feature branch before merging: combine WIP commits, fix messages. Never rebase already-pushed commits.",
    ),
    Question(
        id="git_013", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you manage large files in Git?",
        expected_keywords=["Git LFS", "large file", "pointer", "binary", ".gitattributes", "storage", "bandwidth", "track", "clone"],
        model_answer_hint="Git LFS (Large File Storage): replaces large files with lightweight pointers in Git, stores actual content on remote server. Configure with .gitattributes (track patterns). Benefits: smaller repo clone, reduced bandwidth. Alternatives: .gitignore large files and use artifact storage. Consider for: binaries, models, datasets, media.",
    ),
    Question(
        id="git_014", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How do you design a monorepo Git strategy for large teams?",
        expected_keywords=["monorepo", "sparse checkout", "CODEOWNERS", "CI", "affected", "scalability", "virtual filesystem", "cache", "ownership"],
        model_answer_hint="Monorepo challenges: scale (clone size, CI time). Solutions: sparse checkout (only needed directories), CODEOWNERS for review routing, affected-based CI (only build/test changed packages), build caching (Turborepo, Nx), virtual filesystem (VFS for Git), commit access controls. Benefits: atomic cross-package changes, shared tooling, consistent versioning.",
    ),
    Question(
        id="git_015", topic="git_advanced", difficulty="easy", category="git",
        question_type="technical",
        text="What is the difference between git reset and git revert?",
        expected_keywords=["reset", "revert", "undo", "history", "new commit", "move HEAD", "safe", "public", "shared"],
        model_answer_hint="git reset: moves HEAD pointer backward (can discard commits). Three modes: --soft (keep changes staged), --mixed (keep in working dir), --hard (discard everything). git revert: creates a NEW commit that undoes a previous one (safe for shared branches). Use reset for local, revert for public/shared branches.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# TESTING QUESTIONS (15)
# ═══════════════════════════════════════════════════════════════════════════════

TESTING_QUESTIONS = [
    Question(
        id="test_001", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What are the different levels of testing (unit, integration, e2e)?",
        expected_keywords=["unit", "integration", "end-to-end", "e2e", "pyramid", "isolated", "system", "scope", "speed", "confidence"],
        model_answer_hint="Testing pyramid: Unit (bottom, most tests—fast, isolated, single function/class), Integration (middle—test component interactions, DB, APIs), E2E (top, fewest—full user workflows, slowest). More units, fewer e2e. Unit for logic, integration for contracts, e2e for critical paths.",
    ),
    Question(
        id="test_002", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is Test-Driven Development (TDD) and what are its benefits?",
        expected_keywords=["TDD", "red-green-refactor", "test first", "design", "regression", "confidence", "documentation", "feedback", "cycle"],
        model_answer_hint="TDD cycle: write failing test (Red) → write minimum code to pass (Green) → refactor (Refactor). Benefits: better design (testable by construction), immediate feedback, regression prevention, living documentation, confidence to refactor. Challenges: learning curve, discipline, slow start initially.",
    ),
    Question(
        id="test_003", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is mocking and when should you use it?",
        expected_keywords=["mock", "stub", "fake", "spy", "isolate", "dependency", "external", "behavior", "verify", "test double"],
        model_answer_hint="Mocking replaces real dependencies with controlled test doubles. Types: stub (returns canned data), mock (verifies interactions), spy (wraps real object, records calls), fake (simplified implementation). Use for: external services, databases, time-dependent code. Don't over-mock—test behavior, not implementation.",
    ),
    Question(
        id="test_004", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test microservices effectively?",
        expected_keywords=["contract testing", "Pact", "integration", "consumer-driven", "service virtualization", "testcontainers", "isolated", "schema"],
        model_answer_hint="Layers: unit tests per service, contract tests (Pact—verify API contracts between services), integration tests with Testcontainers (real DBs), component tests (service + dependencies), e2e for critical flows. Service virtualization for unavailable dependencies. Consumer-driven contracts prevent breaking changes.",
    ),
    Question(
        id="test_005", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="What is property-based testing and how does it differ from example-based testing?",
        expected_keywords=["property-based", "Hypothesis", "QuickCheck", "generate", "invariant", "edge case", "shrinking", "random", "property"],
        model_answer_hint="Example-based: specific input/output pairs. Property-based: define properties (invariants) that should hold for ALL inputs, framework generates random inputs to find violations. Finds edge cases you wouldn't think of. Shrinking minimizes failing case. Tools: Hypothesis (Python), QuickCheck. Example: 'sort(x) has same length as x and is ordered'.",
    ),
    Question(
        id="test_006", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you achieve good test coverage without sacrificing test quality?",
        expected_keywords=["coverage", "mutation testing", "meaningful", "behavior", "branch", "path", "quality", "maintenance", "critical"],
        model_answer_hint="Coverage metrics: line, branch, path coverage. High coverage ≠ good tests (can have assertions that never fail). Prefer: test critical paths, edge cases, error handling. Mutation testing (introduce bugs, verify tests catch them) measures test quality. Focus on behavior coverage, not line coverage. 80% is often a good target.",
    ),
    Question(
        id="test_007", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you write tests for asynchronous code?",
        expected_keywords=["async", "await", "callback", "promise", "timeout", "polling", "mock timer", "event", "assertion"],
        model_answer_hint="Approaches: async/await in test functions (most frameworks support), mock timers (jest.useFakeTimers, freezegun), wait for assertions (polling with timeout), flush promises/microtasks, test event emissions. Common mistakes: forgetting await, tests passing due to timeout instead of assertion, flaky timing.",
    ),
    Question(
        id="test_008", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="What is chaos engineering and how does it relate to testing?",
        expected_keywords=["chaos engineering", "resilience", "failure injection", "Netflix", "Chaos Monkey", "hypothesis", "blast radius", "steady state", "production"],
        model_answer_hint="Chaos engineering: deliberately inject failures to verify system resilience. Process: define steady state → hypothesize impact → run experiment (controlled blast radius) → observe → improve. Examples: kill instances, network latency, disk full. Netflix's Chaos Monkey. Differs from testing: run in production (or production-like), tests unknown unknowns.",
    ),
    Question(
        id="test_009", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you handle test data management effectively?",
        expected_keywords=["fixture", "factory", "seed", "isolation", "cleanup", "builder pattern", "deterministic", "shared", "database"],
        model_answer_hint="Strategies: factories/builders for flexible test data creation, fixtures for shared setup, database transactions for isolation (rollback after test), seeded randomness for reproducibility, test data builders. Avoid shared mutable state between tests. Each test should set up its own data. Use realistic but anonymized data.",
    ),
    Question(
        id="test_010", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you design a comprehensive testing strategy for a CI/CD pipeline?",
        expected_keywords=["CI/CD", "pipeline", "parallel", "smoke", "regression", "gate", "fast feedback", "flaky", "environment"],
        model_answer_hint="Pipeline stages: 1) lint + unit tests (fast, <5min gate), 2) integration tests (parallel execution), 3) e2e smoke tests (critical paths), 4) deploy to staging, 5) full regression. Handle flaky tests (quarantine, retry). Parallel execution for speed. Test environment parity with production. Canary deployment + automated rollback.",
    ),
    Question(
        id="test_011", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you test distributed systems for consistency and correctness?",
        expected_keywords=["distributed", "Jepsen", "linearizability", "partition", "clock", "deterministic simulation", "trace", "model checking"],
        model_answer_hint="Approaches: Jepsen testing (test consistency under network partitions/clock skew), deterministic simulation (simulate network, inject faults reproducibly), model checking (TLA+ for formal verification), trace-based testing (record/replay distributed events), chaos testing in staging. Test for: linearizability, partition tolerance, recovery correctness.",
    ),
    Question(
        id="test_012", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What makes a good unit test?",
        expected_keywords=["isolated", "fast", "repeatable", "readable", "one assertion", "arrange-act-assert", "independent", "descriptive name"],
        model_answer_hint="Good unit test: fast, isolated (no external dependencies), repeatable (deterministic), independent (order doesn't matter), descriptive name (documents behavior), single responsibility (one reason to fail), readable (AAA: Arrange-Act-Assert). Tests should be as important as production code.",
    ),
    Question(
        id="test_013", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test database interactions?",
        expected_keywords=["repository", "testcontainers", "transaction", "rollback", "in-memory", "migration", "fixture", "isolation", "integration"],
        model_answer_hint="Options: Testcontainers (real DB in Docker—most realistic), in-memory DB (SQLite for simple cases), transaction rollback (wrap each test, rollback after). Test: queries, migrations, constraints, triggers. Use repository pattern to isolate DB access. Separate from unit tests (integration test suite). Seed consistent test data.",
    ),
    Question(
        id="test_014", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you deal with flaky tests in a large test suite?",
        expected_keywords=["flaky", "retry", "quarantine", "root cause", "timing", "ordering", "isolation", "shared state", "detection"],
        model_answer_hint="Detection: track test pass rate over time, automatic flaky detection (passes on retry). Management: quarantine flaky tests (separate suite, don't block CI). Root causes: shared state between tests, timing/race conditions, external dependencies, test ordering. Fixes: better isolation, deterministic waits (not sleep), mock time, remove shared state.",
    ),
    Question(
        id="test_015", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="What is load testing and how do you design load tests?",
        expected_keywords=["load testing", "JMeter", "k6", "Locust", "concurrent users", "throughput", "latency", "saturation", "baseline", "ramp-up"],
        model_answer_hint="Load testing verifies system performance under expected/peak load. Design: define SLOs (p99 latency, throughput), identify critical user journeys, ramp up gradually (find breaking point), measure under sustained load. Tools: k6, Locust, JMeter. Types: load (expected), stress (beyond limit), spike (sudden surge), soak (sustained).",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY QUESTIONS (15)
# ═══════════════════════════════════════════════════════════════════════════════

SECURITY_QUESTIONS = [
    Question(
        id="sec_001", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is the OWASP Top 10 and why is it important?",
        expected_keywords=["OWASP", "Top 10", "injection", "broken authentication", "XSS", "vulnerability", "web security", "awareness", "standard"],
        model_answer_hint="OWASP Top 10: most critical web application security risks. Includes: injection, broken authentication, sensitive data exposure, XML external entities, broken access control, security misconfiguration, XSS, insecure deserialization, vulnerable components, insufficient logging. Industry standard awareness document. Update periodically.",
    ),
    Question(
        id="sec_002", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="How does HTTPS work? Explain the TLS handshake.",
        expected_keywords=["HTTPS", "TLS", "handshake", "certificate", "encryption", "symmetric", "asymmetric", "CA", "public key"],
        model_answer_hint="TLS handshake: 1) Client Hello (supported ciphers), 2) Server Hello (chosen cipher + certificate), 3) Client verifies certificate (CA chain), 4) Key exchange (asymmetric) to establish shared secret, 5) Symmetric encryption for data (AES). Provides: confidentiality, integrity, authentication. Certificate from trusted CA proves server identity.",
    ),
    Question(
        id="sec_003", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is SQL injection and how do you prevent it?",
        expected_keywords=["SQL injection", "parameterized", "prepared statement", "input validation", "escape", "ORM", "sanitize", "user input"],
        model_answer_hint="SQL injection: attacker manipulates SQL queries through unsanitized input. Example: ' OR 1=1 --. Prevention: parameterized queries/prepared statements (separate data from code), ORMs, input validation, least privilege DB accounts, WAF. Never concatenate user input into SQL strings.",
    ),
    Question(
        id="sec_004", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="Explain the difference between authentication and authorization.",
        expected_keywords=["authentication", "authorization", "identity", "permission", "who", "what", "access control", "verify", "grant"],
        model_answer_hint="Authentication (AuthN): verifying WHO someone is (identity). Methods: password, MFA, biometrics, certificates. Authorization (AuthZ): determining WHAT they can access (permissions). Methods: RBAC, ABAC, ACL, policies. Authentication happens first, then authorization. Both are required for secure systems.",
    ),
    Question(
        id="sec_005", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you securely store passwords?",
        expected_keywords=["hash", "bcrypt", "salt", "argon2", "scrypt", "one-way", "never plaintext", "work factor", "rainbow table"],
        model_answer_hint="Never store plaintext. Use: strong hashing with salt (bcrypt, argon2, scrypt). Salt prevents rainbow table attacks (unique per password). Work factor makes brute-force expensive. Never use MD5/SHA for passwords (too fast). Argon2id is current recommendation. Implement account lockout and rate limiting for login attempts.",
    ),
    Question(
        id="sec_006", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="Explain XSS (Cross-Site Scripting) attacks and prevention.",
        expected_keywords=["XSS", "stored", "reflected", "DOM", "sanitize", "escape", "Content-Security-Policy", "encoding", "cookie HttpOnly"],
        model_answer_hint="XSS types: Stored (persisted in DB), Reflected (in URL/request), DOM-based (client-side). Attacker injects scripts to steal cookies/credentials, deface, redirect. Prevention: output encoding/escaping (context-aware), Content-Security-Policy header, HttpOnly cookies, input validation, DOMPurify for user HTML, avoid innerHTML.",
    ),
    Question(
        id="sec_007", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How does OAuth 2.0 work? Explain the authorization code flow.",
        expected_keywords=["OAuth", "authorization code", "token", "redirect", "scope", "client", "resource server", "access token", "refresh token", "PKCE"],
        model_answer_hint="Authorization Code flow: 1) Client redirects user to auth server, 2) User authenticates and consents to scopes, 3) Auth server redirects back with authorization code, 4) Client exchanges code for access token (server-to-server), 5) Use access token for API calls. PKCE extension prevents code interception for public clients. Refresh tokens for longevity.",
    ),
    Question(
        id="sec_008", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="What is CSRF and how do you prevent it?",
        expected_keywords=["CSRF", "cross-site request forgery", "token", "SameSite", "cookie", "origin", "state-changing", "synchronizer token"],
        model_answer_hint="CSRF: attacker tricks authenticated user's browser into making unwanted request. Prevention: CSRF tokens (synchronizer token pattern—unique per session/request), SameSite cookie attribute (Strict/Lax), check Origin/Referer headers, require custom headers for APIs. Only state-changing requests (POST/PUT/DELETE) are vulnerable.",
    ),
    Question(
        id="sec_009", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you implement JWT (JSON Web Tokens) securely?",
        expected_keywords=["JWT", "header", "payload", "signature", "secret", "expiration", "stateless", "refresh", "algorithm", "validate"],
        model_answer_hint="JWT structure: header.payload.signature (base64 encoded). Security: use strong algorithm (RS256 > HS256 for distributed), short expiration (15-60 min), validate signature + expiration + issuer + audience, use refresh tokens for renewal, don't store sensitive data in payload (base64 is NOT encryption), revocation strategy.",
    ),
    Question(
        id="sec_010", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="What are common API security vulnerabilities and how do you address them?",
        expected_keywords=["authentication", "rate limiting", "input validation", "injection", "broken access", "mass assignment", "BOLA", "logging"],
        model_answer_hint="Common API vulnerabilities (OWASP API Security): Broken Object Level Authorization (BOLA—access others' resources), broken authentication, excessive data exposure, lack of rate limiting, broken function-level authorization, mass assignment, injection. Mitigations: auth on every endpoint, input validation, output filtering, rate limiting, logging, WAF.",
    ),
    Question(
        id="sec_011", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you implement a zero-trust security architecture?",
        expected_keywords=["zero trust", "verify", "least privilege", "microsegmentation", "continuous", "identity", "context", "encrypt", "assume breach"],
        model_answer_hint="Zero trust principles: never trust, always verify. Implementation: strong identity for all users/services (mTLS, SPIFFE), microsegmentation (fine-grained network policies), least privilege access, continuous verification (not just at login), encrypt all traffic (even internal), assume breach (detect + contain), context-aware access decisions (device, location, behavior).",
    ),
    Question(
        id="sec_012", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you perform a security code review?",
        expected_keywords=["code review", "SAST", "vulnerability", "injection", "authentication", "authorization", "secrets", "dependency", "checklist"],
        model_answer_hint="Focus areas: input validation (all entry points), authentication/authorization logic, secrets management (no hardcoded), SQL/command injection, XSS in templates, cryptography usage, error handling (no info leakage), dependency vulnerabilities (SCA tools). Use SAST tools (Semgrep, CodeQL) + manual review for business logic. Check access control on every endpoint.",
    ),
    Question(
        id="sec_013", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you secure a CI/CD pipeline?",
        expected_keywords=["CI/CD", "secrets", "scanning", "SBOM", "signing", "least privilege", "artifact", "supply chain", "SLSA"],
        model_answer_hint="Secure CI/CD: secrets management (vault, not env vars in code), SAST/DAST scanning in pipeline, dependency scanning (SCA), container image scanning, artifact signing (cosign, SLSA provenance), least privilege for CI accounts, pin actions/dependencies to SHA, protect main branch, audit logs, SBOM generation.",
    ),
    Question(
        id="sec_014", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you handle security incident response?",
        expected_keywords=["incident response", "contain", "eradicate", "recover", "detect", "lessons learned", "playbook", "communication", "triage"],
        model_answer_hint="IR phases (NIST): 1) Preparation (playbooks, tools, training), 2) Detection & Analysis (triage severity, determine scope), 3) Containment (stop bleeding—isolate affected systems), 4) Eradication (remove threat, patch vulnerability), 5) Recovery (restore services, verify clean), 6) Post-Incident (lessons learned, improve). Communication plan for stakeholders.",
    ),
    Question(
        id="sec_015", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="What is Content Security Policy (CSP) and how do you implement it?",
        expected_keywords=["CSP", "Content-Security-Policy", "directive", "script-src", "XSS", "inline", "nonce", "report", "whitelist"],
        model_answer_hint="CSP: HTTP header that restricts which resources a page can load (scripts, styles, images, etc.). Directives: script-src, style-src, img-src, connect-src, default-src. Use nonce or hash for inline scripts (avoid 'unsafe-inline'). report-uri for monitoring violations. Start with report-only mode, then enforce. Powerful XSS mitigation.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL / HR QUESTIONS (40)
# ═══════════════════════════════════════════════════════════════════════════════

BEHAVIORAL_QUESTIONS = [
    # --- EASY (general, all levels) ---
    Question(
        id="hr_001", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="Tell me about yourself and your background in software development.",
        expected_keywords=["experience", "skills", "passion", "growth", "project", "team", "technology", "contribution", "goal"],
        model_answer_hint="Structure: current role → key experience highlights → why this role interests you. Focus on relevant experience, technical growth, and impact. Keep to 2-3 minutes. Show progression and enthusiasm.",
    ),
    Question(
        id="hr_002", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="Why are you interested in this position?",
        expected_keywords=["company", "role", "growth", "challenge", "technology", "team", "mission", "impact", "skills", "opportunity"],
        model_answer_hint="Show research: mention specific company values/products. Connect your skills to role requirements. Express genuine interest in their tech stack/challenges. Mention growth opportunities and how you'd contribute.",
    ),
    Question(
        id="hr_003", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="What are your greatest strengths as a developer?",
        expected_keywords=["strength", "example", "impact", "problem-solving", "communication", "learning", "team", "technical", "adaptable"],
        model_answer_hint="Pick 2-3 strengths relevant to the role. For each: name it, give specific example showing it in action, describe the positive impact. Balance technical (debugging, architecture) with soft skills (communication, mentoring).",
    ),
    Question(
        id="hr_004", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="Where do you see yourself in 5 years?",
        expected_keywords=["growth", "leadership", "technical", "expert", "contribute", "mentor", "impact", "learning", "architecture"],
        model_answer_hint="Show ambition aligned with realistic growth. Options: technical leadership (staff/principal engineer), people management, deep specialization. Express desire to grow with the company. Show you've thought about your career path.",
    ),
    Question(
        id="hr_005", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="How do you stay current with technology trends?",
        expected_keywords=["learning", "reading", "conference", "side project", "community", "blog", "course", "experiment", "open source"],
        model_answer_hint="Mention specific strategies: tech blogs/newsletters, conferences, side projects to try new tech, open source contribution, online courses, tech communities, reading source code of interesting projects. Show continuous learning mindset with specific recent examples.",
    ),
    # --- MEDIUM (situational, STAR format) ---
    Question(
        id="hr_006", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a time you had to debug a critical production issue under pressure.",
        expected_keywords=["situation", "pressure", "systematic", "logs", "root cause", "communication", "resolution", "prevention", "postmortem"],
        model_answer_hint="STAR format: Situation (what broke, impact), Task (your role), Action (systematic debugging—logs, metrics, reproduction, isolation), Result (resolution time, prevention steps). Show calm under pressure, communication with stakeholders, and postmortem/prevention focus.",
    ),
    Question(
        id="hr_007", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you disagreed with a technical decision. How did you handle it?",
        expected_keywords=["disagree", "data", "perspective", "compromise", "respectful", "evidence", "outcome", "learn", "team"],
        model_answer_hint="Show: respectful disagreement with data/evidence, willingness to listen to other perspectives, focus on best outcome (not being right), compromise or commit after decision. Demonstrate maturity—sometimes you were wrong, sometimes you convinced others.",
    ),
    Question(
        id="hr_008", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a project where you had to learn a new technology quickly.",
        expected_keywords=["learn", "fast", "research", "practice", "mentor", "documentation", "prototype", "apply", "deadline"],
        model_answer_hint="Show learning strategy: research (docs, tutorials, source code), hands-on practice (prototype/side project), ask experts, apply incrementally. Emphasize speed of ramp-up and successful delivery. Demonstrate adaptability and learning methodology.",
    ),
    Question(
        id="hr_009", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you had to work with a difficult team member.",
        expected_keywords=["communication", "empathy", "understanding", "professional", "resolution", "feedback", "adapt", "perspective", "outcome"],
        model_answer_hint="Show emotional intelligence: understand their perspective, communicate directly and respectfully, find common ground, focus on shared goals, involve manager if needed. Don't badmouth—focus on what you learned and how the relationship improved. Show you can work with diverse personalities.",
    ),
    Question(
        id="hr_010", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe your approach to estimating and meeting deadlines.",
        expected_keywords=["estimation", "breakdown", "buffer", "communicate", "track", "risk", "prioritize", "scope", "realistic"],
        model_answer_hint="Approach: break down into smaller tasks, estimate each, add buffer for unknowns, track progress, communicate early if at risk. Discuss: handling scope creep (negotiate), re-prioritization, MVP approach, stakeholder communication. Show reliability and proactive risk management.",
    ),
    Question(
        id="hr_011", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you received constructive criticism. How did you respond?",
        expected_keywords=["feedback", "growth", "open", "improve", "action", "grateful", "change", "self-awareness", "professional"],
        model_answer_hint="Show openness to feedback: listened without defensiveness, asked clarifying questions, reflected honestly, took specific action to improve, followed up to verify improvement. Demonstrate growth mindset—criticism is a gift. Give specific example of change made.",
    ),
    Question(
        id="hr_012", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a situation where you had to balance technical debt with feature delivery.",
        expected_keywords=["technical debt", "trade-off", "prioritize", "business value", "risk", "plan", "refactor", "communicate", "stakeholder"],
        model_answer_hint="Show judgment: quantify debt impact (velocity, bugs, risk), communicate to stakeholders in business terms, propose balanced approach (allocate % for debt reduction, address critical debt with features, boy scout rule). Demonstrate ability to make pragmatic trade-offs while advocating for quality.",
    ),
    Question(
        id="hr_013", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="How do you mentor junior developers?",
        expected_keywords=["mentor", "pair programming", "code review", "patience", "encourage", "growth", "autonomous", "guide", "feedback"],
        model_answer_hint="Approaches: pair programming, thoughtful code reviews (explain why), create safe space for questions, provide increasing autonomy, set clear expectations, celebrate progress, share resources. Balance guiding vs. letting them struggle (productive struggle builds skills). Document patterns/decisions for team learning.",
    ),
    Question(
        id="hr_014", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you improved a process or workflow on your team.",
        expected_keywords=["improvement", "identify", "propose", "implement", "measure", "team buy-in", "automation", "efficiency", "result"],
        model_answer_hint="STAR: identify pain point (data/observations), propose solution with evidence, get team buy-in, implement incrementally, measure improvement (time saved, errors reduced). Examples: CI/CD improvements, code review process, documentation, automated testing, on-call rotation.",
    ),
    Question(
        id="hr_015", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a time you made a mistake at work. What happened and what did you learn?",
        expected_keywords=["mistake", "accountability", "learn", "fix", "prevent", "honest", "impact", "growth", "process"],
        model_answer_hint="Show accountability: own the mistake, describe impact honestly, explain how you fixed it, what you learned, and what you changed to prevent recurrence. Don't pick a trivial mistake—show vulnerability and genuine learning. Demonstrate that you create systemic fixes (not just personal ones).",
    ),
    # --- HARDER (leadership, complex scenarios) ---
    Question(
        id="hr_016", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Describe a time you had to make a decision with incomplete information.",
        expected_keywords=["uncertainty", "risk", "analysis", "decision", "reversible", "data", "intuition", "outcome", "adapt"],
        model_answer_hint="Show decision-making framework: assess what you know and don't, evaluate risks, consider reversibility (two-way door decisions), gather available data quickly, make the call, monitor and adapt. Demonstrate comfort with ambiguity and ability to move forward without perfect information.",
    ),
    Question(
        id="hr_017", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Tell me about a time you led a complex cross-team project.",
        expected_keywords=["leadership", "coordination", "stakeholder", "communication", "alignment", "dependency", "risk", "delivery", "influence"],
        model_answer_hint="Demonstrate: clear communication across teams, managing dependencies, aligning different priorities, influence without authority, tracking progress, risk mitigation, adapting to changes. Show how you created shared understanding of goals and maintained momentum across organizational boundaries.",
    ),
    Question(
        id="hr_018", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="How do you approach making architectural decisions that will affect the team for years?",
        expected_keywords=["trade-off", "reversibility", "requirements", "team input", "document", "prototype", "ADR", "principles", "future"],
        model_answer_hint="Process: gather requirements (current + future scale), evaluate options with trade-offs, get team input (RFC/design doc), prototype if uncertain, document decision rationale (ADR), build for change (modular, interfaces). Consider: team skills, operational complexity, total cost. Prefer reversible decisions where possible.",
    ),
    Question(
        id="hr_019", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Describe how you've built engineering culture or influenced team practices.",
        expected_keywords=["culture", "practice", "influence", "lead by example", "documentation", "standards", "collaboration", "improvement", "adoption"],
        model_answer_hint="Show influence: leading by example (write tests, good PRs, documentation), proposing and building consensus for new practices, creating templates/tools that make good practices easy, mentoring, celebrating quality wins. Culture change is gradual—show patience and persistence. Measure impact.",
    ),
    Question(
        id="hr_020", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Tell me about a time you had to push back on a stakeholder's request.",
        expected_keywords=["pushback", "stakeholder", "alternative", "trade-off", "negotiate", "data", "scope", "technical feasibility", "compromise"],
        model_answer_hint="Show diplomatic pushback: understand their underlying need (not just request), explain trade-offs and risks clearly, propose alternatives that meet the real need, back with data/evidence. Demonstrate: protecting team from unsustainable commitments while maintaining strong stakeholder relationships.",
    ),
    Question(
        id="hr_021", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="How do you handle stress and tight deadlines?",
        expected_keywords=["prioritize", "focus", "communicate", "break down", "self-care", "team", "realistic", "scope", "calm"],
        model_answer_hint="Strategies: prioritize ruthlessly (what's essential vs nice-to-have), break work into smaller deliverables, communicate early if deadline is at risk, ask for help, maintain perspective and self-care (prevent burnout). Show you remain effective under pressure without sacrificing quality or team health.",
    ),
    Question(
        id="hr_022", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe your ideal development team culture.",
        expected_keywords=["collaboration", "trust", "feedback", "learning", "ownership", "psychological safety", "accountability", "diversity", "quality"],
        model_answer_hint="Elements: psychological safety (safe to take risks, ask questions), ownership and accountability, blameless postmortems, continuous learning, constructive feedback culture, collaboration over competition, diverse perspectives valued, code quality pride, work-life balance. Show you actively contribute to creating such culture.",
    ),
    Question(
        id="hr_023", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you had to onboard into a large existing codebase.",
        expected_keywords=["onboard", "codebase", "read", "ask", "incremental", "documentation", "small changes", "understand", "contribute"],
        model_answer_hint="Strategy: start with documentation/architecture docs, set up and run locally, read tests (they document behavior), start with small bugs/tasks, ask questions (identify knowledgeable teammates), trace request flows, take notes. Show you can become productive in unfamiliar codebases quickly and systematically.",
    ),
    Question(
        id="hr_024", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="How do you approach code reviews, both giving and receiving?",
        expected_keywords=["constructive", "respectful", "learn", "suggest", "explain", "approve", "nitpick", "blocking", "praise"],
        model_answer_hint="Giving: be constructive (suggest, don't demand), explain why, distinguish blocking vs. nitpick, praise good patterns, timely reviews. Receiving: be open and not defensive, ask questions for clarity, iterate quickly, treat as learning opportunity. Goal: improve code quality AND spread knowledge across team.",
    ),
    Question(
        id="hr_025", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a time you had to communicate a complex technical concept to a non-technical audience.",
        expected_keywords=["simplify", "analogy", "visual", "audience", "jargon-free", "context", "impact", "question", "understand"],
        model_answer_hint="Techniques: use analogies from everyday life, visual diagrams, focus on impact/outcome (not implementation), avoid jargon (or define it), check understanding, encourage questions, tell a story. Show you can adapt communication style to audience. This skill is crucial for stakeholder buy-in.",
    ),
    Question(
        id="hr_026", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Tell me about a project that failed. What did you learn?",
        expected_keywords=["failure", "learn", "accountability", "root cause", "improve", "adapt", "communication", "retrospective", "prevent"],
        model_answer_hint="Show honest reflection: what happened (without blame), your role in the failure, root causes identified, what you personally learned, how you've applied those lessons since. Demonstrate growth mindset—failure as learning opportunity. Show the systemic changes you advocated for afterward.",
    ),
    Question(
        id="hr_027", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="What motivates you as a software developer?",
        expected_keywords=["problem-solving", "impact", "learning", "craft", "team", "user", "challenge", "growth", "build"],
        model_answer_hint="Authentic answers: solving complex problems, seeing users benefit from your work, continuous learning, craftsmanship pride, working with talented teammates, making processes better, building something from nothing. Connect motivation to the specific role/company.",
    ),
    Question(
        id="hr_028", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="How do you handle scope creep in a project?",
        expected_keywords=["scope", "creep", "boundary", "prioritize", "negotiate", "MVP", "backlog", "communicate", "trade-off", "stakeholder"],
        model_answer_hint="Approach: recognize creep early, document original scope, evaluate new requests (effort + value), communicate trade-offs (this delays that), negotiate (defer to backlog, reduce scope elsewhere, extend timeline). Protect team from endless expansion while remaining flexible for genuinely important changes. MoSCoW prioritization.",
    ),
    Question(
        id="hr_029", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe how you approach working in a remote or distributed team.",
        expected_keywords=["communication", "async", "documentation", "timezone", "proactive", "video", "visibility", "trust", "overlap"],
        model_answer_hint="Remote work practices: over-communicate (written updates, async-first), documentation as source of truth, clear meeting agendas, respect timezones, proactive status sharing, build relationships (virtual coffee chats), maintain visibility of work (PRs, updates), trust-based culture. Show you thrive in remote settings.",
    ),
    Question(
        id="hr_030", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="How do you balance perfection with pragmatism in software engineering?",
        expected_keywords=["pragmatic", "trade-off", "good enough", "iterate", "business value", "quality", "time-to-market", "refactor later", "context"],
        model_answer_hint="Framework: consider context (prototype vs. critical infrastructure), focus on reversibility (can we improve later?), ship and iterate, define 'good enough' (must-have quality vs. nice-to-have polish). Quality non-negotiables: security, data integrity, test coverage for critical paths. Everything else is a trade-off. Communicate trade-offs explicitly.",
    ),
    Question(
        id="hr_031", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="What type of work environment do you thrive in?",
        expected_keywords=["collaborative", "autonomous", "flexible", "learning", "fast-paced", "structured", "feedback", "trust", "growth"],
        model_answer_hint="Be honest and specific. Mention: collaboration style (pair programming, async), autonomy level, feedback frequency, pace preference, learning opportunities. Connect to the company's known culture. Show self-awareness about what makes you most productive and happy.",
    ),
    Question(
        id="hr_032", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Tell me about a time you had to advocate for a technical investment with business stakeholders.",
        expected_keywords=["advocate", "business case", "ROI", "risk", "technical debt", "translate", "metrics", "non-technical", "buy-in"],
        model_answer_hint="Translate technical to business: frame in terms of risk (outage probability, security), velocity (team speed impact), cost (operational expense), customer impact. Quantify where possible. Propose incremental approach. Show you can bridge technical and business perspectives effectively.",
    ),
    Question(
        id="hr_033", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="How do you handle ethical dilemmas in software development?",
        expected_keywords=["ethics", "privacy", "user", "principle", "speak up", "responsibility", "impact", "stakeholder", "transparency"],
        model_answer_hint="Framework: consider user impact, privacy, fairness, transparency. Actions: raise concerns early, propose alternatives, document objections if overruled, know your red lines. Examples: dark patterns, biased algorithms, privacy violations. Show you think beyond code to societal impact and have moral courage to speak up.",
    ),
    Question(
        id="hr_034", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="Do you have any questions for us?",
        expected_keywords=["question", "culture", "team", "growth", "challenge", "technology", "roadmap", "success", "day-to-day"],
        model_answer_hint="Good questions to ask: team culture and collaboration, biggest current challenges, tech stack and decisions, growth and learning opportunities, how success is measured, typical day-to-day, recent architectural decisions, on-call expectations. Shows genuine interest and evaluates mutual fit.",
    ),
    Question(
        id="hr_035", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="Describe a time you had to deliver bad news to a stakeholder or team.",
        expected_keywords=["honest", "early", "solution", "transparency", "empathy", "alternative", "plan", "trust", "proactive"],
        model_answer_hint="Approach: deliver bad news early (not last minute), be transparent and honest, come with analysis and proposed solutions/alternatives, show empathy for impact, take accountability where appropriate. Build trust through candor. Stakeholders respect honesty over false optimism.",
    ),
    Question(
        id="hr_036", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="How do you prioritize competing tasks and requests?",
        expected_keywords=["prioritize", "urgent", "important", "impact", "communicate", "delegate", "time management", "focus", "matrix"],
        model_answer_hint="Framework: urgent vs. important matrix, business impact assessment, dependencies (what blocks others), communicate trade-offs to stakeholders, set expectations on timing, batch similar work, protect focus time for deep work. Show you can say 'not now' while maintaining relationships.",
    ),
    Question(
        id="hr_037", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Tell me about a time you drove a significant technical migration.",
        expected_keywords=["migration", "planning", "incremental", "risk", "rollback", "testing", "stakeholder", "success metrics", "team alignment"],
        model_answer_hint="Show: thorough planning (assess scope, identify risks), incremental approach (strangler fig, feature flags), testing strategy (parallel run, shadow traffic), rollback plan, team alignment and communication, success metrics, stakeholder management. Demonstrate you can drive large-scale technical change safely.",
    ),
    Question(
        id="hr_038", topic="behavioral", difficulty="easy", category="behavioral",
        question_type="hr",
        text="What's your approach to writing documentation?",
        expected_keywords=["documentation", "audience", "up-to-date", "ADR", "README", "decision", "why", "maintain", "clear"],
        model_answer_hint="Document the 'why' not just the 'what': decision records (ADRs), architecture diagrams, README for onboarding, runbooks for operations. Keep close to code (it stays updated). Audience-appropriate (developer docs vs. user docs). Treat documentation as part of the deliverable, not afterthought.",
    ),
    Question(
        id="hr_039", topic="behavioral", difficulty="medium", category="behavioral",
        question_type="hr",
        text="How do you handle disagreements about code quality standards on a team?",
        expected_keywords=["standards", "agreement", "automated", "linter", "team decision", "document", "objective", "consistent", "pragmatic"],
        model_answer_hint="Approach: codify standards in linter/formatter (remove subjective debates), team discussion for important patterns (write style guide), accept team decisions you disagree with, propose changes through proper channels (RFC/tech talk), pick battles. Objective: consistency matters more than personal preference.",
    ),
    Question(
        id="hr_040", topic="behavioral", difficulty="hard", category="behavioral",
        question_type="hr",
        text="Describe how you would build a new engineering team from scratch.",
        expected_keywords=["hiring", "culture", "values", "process", "tools", "ramp-up", "architecture", "documentation", "communication", "diversity"],
        model_answer_hint="Build foundation first: define team values/culture, choose tech stack thoughtfully (hire for existing skills vs. ideal tech), establish development practices early (CI/CD, testing, code review), document decisions, create onboarding process, hire diverse perspectives, foster psychological safety. Start with strong senior hires who can multiply.",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL DOCKER/KUBERNETES QUESTIONS (7)
# ═══════════════════════════════════════════════════════════════════════════════

DOCKER_EXTRA_QUESTIONS = [
    Question(
        id="docker_026", topic="docker_advanced", difficulty="medium", category="docker",
        question_type="technical",
        text="How do you manage environment-specific configurations in Docker?",
        expected_keywords=["env file", "environment variable", "docker-compose", "override", "secrets", "config map", "build arg", "runtime"],
        model_answer_hint="Use .env files with docker-compose, environment variables at runtime, build args for build-time config, docker secrets for sensitive data. Override files (docker-compose.override.yml) for environment-specific settings. Never bake secrets into images.",
    ),
    Question(
        id="docker_027", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement resource quotas and limit ranges in Kubernetes?",
        expected_keywords=["ResourceQuota", "LimitRange", "namespace", "CPU", "memory", "request", "limit", "QoS", "eviction"],
        model_answer_hint="ResourceQuota: limits total resources per namespace (CPU, memory, object count). LimitRange: sets default and max/min per pod/container. QoS classes: Guaranteed (request=limit), Burstable, BestEffort. Eviction order: BestEffort first. Set requests for scheduling, limits for protection.",
    ),
    Question(
        id="docker_028", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="What are Kubernetes Operators and when would you build one?",
        expected_keywords=["Operator", "CRD", "custom resource", "controller", "reconciliation", "domain knowledge", "automate", "lifecycle"],
        model_answer_hint="Operators extend Kubernetes with domain-specific knowledge. Combine CRDs (Custom Resource Definitions) with custom controllers that implement reconciliation loops. Build for: complex stateful applications (databases), automated operational tasks (backups, scaling), encoding operational runbooks as code.",
    ),
    Question(
        id="docker_029", topic="docker_advanced", difficulty="easy", category="docker",
        question_type="technical",
        text="What is the difference between CMD and ENTRYPOINT in Dockerfile?",
        expected_keywords=["CMD", "ENTRYPOINT", "default", "override", "exec form", "shell form", "arguments", "container"],
        model_answer_hint="ENTRYPOINT: the main executable (harder to override, use exec form). CMD: default arguments to ENTRYPOINT (easily overridden at runtime). Together: ENTRYPOINT sets the command, CMD sets default args. Shell form vs exec form: exec form preferred (no shell, proper signal handling).",
    ),
    Question(
        id="docker_030", topic="kubernetes", difficulty="hard", category="docker",
        question_type="technical",
        text="How do you implement pod-to-pod encryption and network policies?",
        expected_keywords=["NetworkPolicy", "mTLS", "service mesh", "Calico", "Cilium", "ingress", "egress", "deny all", "label selector"],
        model_answer_hint="Network Policies: deny-all default, then allow specific ingress/egress by label selector. CNI plugins (Calico, Cilium) enforce policies. For encryption: service mesh mTLS (Istio/Linkerd auto-encrypts pod-to-pod). WireGuard-based CNI encryption (Cilium). Defense in depth: policies + encryption + RBAC.",
    ),
    Question(
        id="docker_031", topic="docker_advanced", difficulty="medium", category="docker",
        question_type="technical",
        text="How do you debug a container that crashes immediately on start?",
        expected_keywords=["logs", "exec", "entrypoint", "override", "sleep", "sh", "inspect", "exit code", "strace"],
        model_answer_hint="Steps: check logs (docker logs), inspect exit code (docker inspect), override entrypoint to get a shell (docker run --entrypoint sh), add sleep to keep container alive for debugging, check file permissions, verify environment variables. In K8s: kubectl logs --previous, ephemeral debug containers.",
    ),
    Question(
        id="docker_032", topic="kubernetes", difficulty="medium", category="docker",
        question_type="technical",
        text="Explain Kubernetes namespaces and their role in multi-team clusters.",
        expected_keywords=["namespace", "isolation", "resource quota", "RBAC", "network policy", "multi-tenant", "default", "kube-system"],
        model_answer_hint="Namespaces provide logical isolation within a cluster: separate resources, RBAC permissions, resource quotas, network policies per namespace. Use for: team separation, environment separation (dev/staging), multi-tenancy. Default namespaces: default, kube-system, kube-public. Not a security boundary alone.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL API DESIGN QUESTIONS (12)
# ═══════════════════════════════════════════════════════════════════════════════

API_EXTRA_QUESTIONS = [
    Question(
        id="api_021", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What are path parameters vs query parameters in REST APIs?",
        expected_keywords=["path", "query", "resource", "filter", "identify", "optional", "required", "URL", "semantics"],
        model_answer_hint="Path parameters identify specific resources (/users/123). Query parameters filter or modify the response (?status=active&sort=name). Path params are typically required, query params optional. Use path for resource identity, query for filtering/sorting/pagination.",
    ),
    Question(
        id="api_022", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What is an API contract and why is it important?",
        expected_keywords=["contract", "specification", "agreement", "breaking change", "versioning", "consumer", "producer", "testing"],
        model_answer_hint="API contract is the agreed-upon interface between consumer and producer: endpoints, request/response formats, error codes, behavior guarantees. Important for: parallel development, preventing breaking changes, generating SDKs, contract testing, documentation. OpenAPI spec is a common contract format.",
    ),
    Question(
        id="api_023", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you handle long-running operations in a REST API?",
        expected_keywords=["async", "polling", "webhook", "202 Accepted", "job", "status endpoint", "callback", "progress", "timeout"],
        model_answer_hint="Pattern: POST returns 202 Accepted with job/task ID and status URL. Client polls status endpoint or registers webhook for completion. Include: progress percentage, estimated time, cancel endpoint. Alternatives: Server-Sent Events for progress streaming. Set reasonable timeouts.",
    ),
    Question(
        id="api_024", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="What is HATEOAS and is it practical for modern APIs?",
        expected_keywords=["HATEOAS", "hypermedia", "links", "discoverability", "self-describing", "REST constraint", "Richardson", "maturity"],
        model_answer_hint="HATEOAS: responses include hypermedia links to related actions/resources. Benefits: self-describing API, clients don't hardcode URLs, API can evolve. Practice: few APIs implement fully. Pragmatic approach: include pagination links, related resource links, and action links for discoverability.",
    ),
    Question(
        id="api_025", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you implement API rate limiting with different tiers?",
        expected_keywords=["tier", "plan", "quota", "burst", "sliding window", "header", "429", "X-RateLimit", "fair usage"],
        model_answer_hint="Implement per-tier limits (free: 100/hr, pro: 10k/hr). Return rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset). Use sliding window algorithm. Allow burst with token bucket. Return 429 with Retry-After. Consider per-endpoint limits for expensive operations.",
    ),
    Question(
        id="api_026", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design an API for file uploads with resumable support?",
        expected_keywords=["chunked", "resumable", "multipart", "offset", "Content-Range", "upload ID", "tus protocol", "progress"],
        model_answer_hint="Resumable upload protocol: 1) POST to get upload URL/ID, 2) PUT chunks with Content-Range header, 3) Server tracks received bytes, 4) Client resumes from last acknowledged offset on failure. Standards: tus protocol. Also support: simple multipart for small files, progress tracking, validation before upload.",
    ),
    Question(
        id="api_027", topic="api_design", difficulty="easy", category="api_design",
        question_type="technical",
        text="What is content negotiation in REST APIs?",
        expected_keywords=["Accept", "Content-Type", "format", "JSON", "XML", "negotiation", "header", "response format"],
        model_answer_hint="Content negotiation: client specifies desired format via Accept header (application/json, application/xml). Server responds with Content-Type indicating actual format. If server can't fulfill, return 406 Not Acceptable. Most modern APIs default to JSON. Support multiple formats for flexibility.",
    ),
    Question(
        id="api_028", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you design an API that supports field selection and expansion?",
        expected_keywords=["fields", "sparse", "expand", "include", "nested", "performance", "over-fetching", "GraphQL-like"],
        model_answer_hint="Field selection: ?fields=id,name,email (return only specified fields, reduce payload). Expansion: ?expand=author,comments (include related resources inline instead of just IDs). Reduces round-trips and over-fetching without full GraphQL complexity. Implement with query parameter parsing and dynamic serialization.",
    ),
    Question(
        id="api_029", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design a streaming API for large datasets?",
        expected_keywords=["streaming", "chunked transfer", "Server-Sent Events", "NDJSON", "backpressure", "cursor", "pagination", "memory"],
        model_answer_hint="Options: chunked transfer encoding (stream line-by-line), NDJSON (newline-delimited JSON), Server-Sent Events (event stream). Handle backpressure (don't overflow client). Use cursor-based iteration for consistent large result sets. Keep memory constant on server (don't load all into memory). Consider gRPC streaming for internal APIs.",
    ),
    Question(
        id="api_030", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="What is API deprecation strategy and how do you communicate it?",
        expected_keywords=["deprecation", "sunset", "header", "migration", "timeline", "warning", "documentation", "changelog"],
        model_answer_hint="Deprecation strategy: announce well in advance (6-12 months), add Sunset header with removal date, add Deprecation header, return deprecation warnings in response, provide migration guide, offer new alternative, monitor usage of deprecated endpoints, communicate via changelog/email/docs.",
    ),
    Question(
        id="api_031", topic="api_design", difficulty="hard", category="api_design",
        question_type="technical",
        text="How do you design an API for a marketplace with complex access control?",
        expected_keywords=["RBAC", "ABAC", "ownership", "scope", "policy", "multi-tenant", "delegation", "resource-based", "hierarchical"],
        model_answer_hint="Combine RBAC (role-based) with ABAC (attribute-based) for fine-grained control. Resource ownership (users own their listings), organization hierarchy (admin > manager > member), delegation (share access), OAuth scopes for API access. Policy engine (OPA/Cedar) for complex rules. Always check authorization at resource level, not just endpoint.",
    ),
    Question(
        id="api_032", topic="api_design", difficulty="medium", category="api_design",
        question_type="technical",
        text="How do you handle API request validation effectively?",
        expected_keywords=["validation", "schema", "JSON Schema", "early fail", "error message", "field-level", "sanitize", "coercion"],
        model_answer_hint="Validate early, fail fast: use JSON Schema or framework validators (Pydantic, Joi) for request body/params. Return field-level errors with clear messages. Validate: types, ranges, required fields, formats (email, URL), relationships between fields. Sanitize inputs. Don't rely on client-side validation alone.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL GIT QUESTIONS (17)
# ═══════════════════════════════════════════════════════════════════════════════

GIT_EXTRA_QUESTIONS = [
    Question(
        id="git_016", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is a pull request and what makes a good one?",
        expected_keywords=["pull request", "review", "description", "small", "focused", "tests", "context", "changelog", "reviewable"],
        model_answer_hint="PR is a request to merge changes with review process. Good PR: small and focused (single concern), clear description (what/why/how), includes tests, references issue/ticket, easy to review (logical commits), screenshots for UI changes. Keep PRs under 400 lines for effective review.",
    ),
    Question(
        id="git_017", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="How do you write good commit messages?",
        expected_keywords=["conventional", "imperative", "subject", "body", "why", "what", "50 characters", "present tense", "atomic"],
        model_answer_hint="Best practices: imperative mood (Add feature, not Added), subject line under 50 chars, blank line before body, body explains why not what. Conventional commits (feat:, fix:, docs:) for automation. Atomic commits (one logical change per commit). Reference issues.",
    ),
    Question(
        id="git_018", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What is git rebase --onto and when would you use it?",
        expected_keywords=["rebase onto", "transplant", "branch", "base", "move", "detach", "range", "commits"],
        model_answer_hint="git rebase --onto <newbase> <oldbase> <branch> transplants commits from one base to another. Use when: branch was based on wrong branch, want to move commits to a different branch, need to remove specific commits from history. More precise than regular rebase.",
    ),
    Question(
        id="git_019", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is .gitignore and how do you use it effectively?",
        expected_keywords=[".gitignore", "ignore", "pattern", "track", "untrack", "global", "template", "build", "dependency"],
        model_answer_hint="gitignore specifies files Git should not track: build outputs, dependencies (node_modules), IDE files, env files, logs. Patterns: *.log, /dist, !important.log. Global gitignore for personal IDE files. Use templates (github/gitignore). Already-tracked files need git rm --cached to stop tracking.",
    ),
    Question(
        id="git_020", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you use git worktrees and what problems do they solve?",
        expected_keywords=["worktree", "multiple", "branch", "checkout", "parallel", "linked", "directory", "switch"],
        model_answer_hint="git worktree: checkout multiple branches simultaneously in separate directories (linked to same repo). Solve: working on feature while doing hotfix without stashing, running tests on one branch while developing on another, comparing branches side-by-side. Lighter than multiple clones.",
    ),
    Question(
        id="git_021", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How do you use git filter-branch or git filter-repo for history rewriting?",
        expected_keywords=["filter-branch", "filter-repo", "rewrite", "history", "remove file", "sensitive", "BFG", "force push"],
        model_answer_hint="git filter-repo (preferred over filter-branch): rewrite entire history. Use for: removing accidentally committed secrets/large files, changing author info, restructuring repositories. BFG Repo-Cleaner for simpler secret/file removal. Always requires force push. Coordinate with team. Consider: is it worth the disruption?",
    ),
    Question(
        id="git_022", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you handle merge commits vs squash merges vs rebase merges?",
        expected_keywords=["merge commit", "squash", "rebase", "linear", "history", "context", "bisect", "clean", "policy"],
        model_answer_hint="Merge commit: preserves full branch history (good for complex features). Squash merge: combines all commits into one (clean main history, loses granular commits). Rebase merge: linear history without merge commits. Trade-offs: bisectability (merge/rebase better), history cleanliness (squash), context preservation (merge). Team should agree on policy.",
    ),
    Question(
        id="git_023", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is git blame and how do you use it for debugging?",
        expected_keywords=["blame", "annotate", "author", "commit", "line", "history", "who", "when", "debug"],
        model_answer_hint="git blame shows who last modified each line and when. Useful for: understanding why code was written a certain way, finding who to ask about specific code, tracking down when a bug was introduced. Use with -L for line range, -w to ignore whitespace changes. Combine with git log for full context.",
    ),
    Question(
        id="git_024", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What are Git submodules and subtrees? When would you use each?",
        expected_keywords=["submodule", "subtree", "repository", "dependency", "nested", "external", "vendor", "sync"],
        model_answer_hint="Submodules: pointer to specific commit in external repo (separate clone, explicit update). Subtrees: merge external repo into subdirectory (single repo, simpler for contributors). Submodules for: strict version pinning, separate development. Subtrees for: simpler workflow, when contributors shouldn't need to know about external repos.",
    ),
    Question(
        id="git_025", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you sign commits and why is it important?",
        expected_keywords=["GPG", "sign", "verify", "trust", "identity", "key", "commit signature", "tag", "SSH"],
        model_answer_hint="Sign commits with GPG or SSH keys to prove authorship. Important for: supply chain security (verify commits aren't forged), compliance requirements, open source trust. Setup: generate GPG key, add to Git config and GitHub. Verify with git log --show-signature. Required in some organizations.",
    ),
    Question(
        id="git_026", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How do you implement a Git-based deployment workflow?",
        expected_keywords=["deployment", "tag", "branch", "CI/CD", "release", "rollback", "environment", "promotion", "artifact"],
        model_answer_hint="Approaches: tag-based releases (tag triggers deploy), branch-per-environment (merge to deploy/production triggers deploy), GitOps (cluster reconciles with git state). Include: automated testing gate, approval for production, rollback strategy (revert commit or redeploy previous tag), artifact versioning tied to commits.",
    ),
    Question(
        id="git_027", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="What is the difference between git fetch and git pull?",
        expected_keywords=["fetch", "pull", "remote", "merge", "download", "update", "local", "tracking", "safe"],
        model_answer_hint="git fetch: downloads changes from remote but doesn't modify local branches (safe, just updates tracking). git pull: fetch + merge (or rebase with --rebase). Fetch is safer—lets you review changes before integrating. Pull is convenient for quick updates. Prefer fetch + merge/rebase for more control.",
    ),
    Question(
        id="git_028", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="How do you clean up old branches in a Git repository?",
        expected_keywords=["prune", "delete", "remote", "merged", "stale", "cleanup", "branch", "list", "automation"],
        model_answer_hint="Local: git branch --merged | xargs git branch -d (delete merged branches). Remote: git remote prune origin (remove stale tracking), git push origin --delete branch-name. Automation: GitHub/GitLab auto-delete on merge, scheduled CI job to clean old branches. Keep main/develop/release branches. Archive with tags if needed.",
    ),
    Question(
        id="git_029", topic="git_advanced", difficulty="hard", category="git",
        question_type="technical",
        text="How do you migrate a large repository to a different Git hosting platform?",
        expected_keywords=["mirror", "clone", "push", "LFS", "history", "CI/CD", "permissions", "hooks", "migration plan"],
        model_answer_hint="Steps: mirror clone (git clone --mirror), push to new remote (git push --mirror). Handle: LFS objects (migrate separately), CI/CD pipeline reconfiguration, branch protection rules, webhooks, access permissions, update developer remotes. Plan: parallel running period, redirect old URLs, communicate timeline to team.",
    ),
    Question(
        id="git_030", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What is git rerere and how does it help with repeated merge conflicts?",
        expected_keywords=["rerere", "reuse", "recorded", "resolution", "conflict", "automatic", "merge", "rebase"],
        model_answer_hint="git rerere (Reuse Recorded Resolution): Git remembers how you resolved merge conflicts and auto-applies the same resolution next time. Enable with git config rerere.enabled true. Useful for: repeated rebases on long-lived branches, cherry-picks across branches. Saves time on recurring conflicts.",
    ),
    Question(
        id="git_031", topic="git_basics", difficulty="easy", category="git",
        question_type="technical",
        text="How do you undo the last commit in Git?",
        expected_keywords=["reset", "revert", "amend", "soft", "mixed", "hard", "undo", "last commit", "HEAD~1"],
        model_answer_hint="Options: git reset --soft HEAD~1 (undo commit, keep changes staged), git reset --mixed HEAD~1 (undo commit, unstage changes), git commit --amend (modify last commit), git revert HEAD (new commit that undoes previous—safe for shared branches). Reset changes history; revert adds to it.",
    ),
    Question(
        id="git_032", topic="git_advanced", difficulty="medium", category="git",
        question_type="technical",
        text="What are Git tags and how do you use them for releases?",
        expected_keywords=["tag", "lightweight", "annotated", "release", "version", "semantic", "push", "signing", "archive"],
        model_answer_hint="Annotated tags: contain metadata (author, date, message)—use for releases. Lightweight tags: just a pointer (bookmarks). Semantic versioning (v1.2.3). Push tags explicitly (git push --tags). CI can trigger release builds on tag creation. Sign tags with GPG for verification. Use for: release points, deployment markers.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL TESTING QUESTIONS (17)
# ═══════════════════════════════════════════════════════════════════════════════

TESTING_EXTRA_QUESTIONS = [
    Question(
        id="test_016", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is the difference between a mock, stub, fake, and spy?",
        expected_keywords=["mock", "stub", "fake", "spy", "test double", "verify", "canned", "behavior", "record"],
        model_answer_hint="Stub: returns canned responses, no verification. Mock: verifies interactions (was method called with correct args?). Fake: working implementation but simplified (in-memory DB). Spy: wraps real object, records calls while executing real logic. All are test doubles replacing real dependencies.",
    ),
    Question(
        id="test_017", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is regression testing and why is it important?",
        expected_keywords=["regression", "existing", "break", "change", "automated", "suite", "CI", "confidence", "refactor"],
        model_answer_hint="Regression testing verifies that new changes don't break existing functionality. Run after every code change. Automated test suites in CI enable safe refactoring. Without regression tests: fear of changing code, accumulating bugs, slower development. They provide confidence that changes are safe.",
    ),
    Question(
        id="test_018", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test error handling and edge cases?",
        expected_keywords=["edge case", "boundary", "error", "exception", "null", "empty", "overflow", "invalid", "negative"],
        model_answer_hint="Test: boundary values (0, -1, MAX_INT), null/undefined/empty inputs, invalid formats, network failures (timeout, 500), concurrent access, overflow/underflow, permission errors. For each function: happy path + error paths + edge cases. Use parameterized tests for multiple edge cases efficiently.",
    ),
    Question(
        id="test_019", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="What is snapshot testing and when is it appropriate?",
        expected_keywords=["snapshot", "serialized", "comparison", "UI", "component", "update", "regression", "brittle", "review"],
        model_answer_hint="Snapshot testing: serialize output (component render, API response), compare against stored snapshot. Appropriate: UI components, serialized data formats, configuration outputs. Risks: brittle (break on any change), large diffs hard to review, false confidence. Best for: catching unintended changes, not verifying correctness.",
    ),
    Question(
        id="test_020", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you implement contract testing between microservices?",
        expected_keywords=["contract", "Pact", "consumer-driven", "provider", "verification", "breaking change", "schema", "CI", "compatibility"],
        model_answer_hint="Consumer-driven contract testing (Pact): consumer defines expected interactions, provider verifies it meets contracts. Flow: consumer generates contract → Pact Broker stores it → provider CI verifies against contracts. Catches breaking changes before deployment. Also: schema validation (OpenAPI), provider contract testing. Integrate into CI to block incompatible changes.",
    ),
    Question(
        id="test_021", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you write tests for third-party API integrations?",
        expected_keywords=["mock", "record", "replay", "VCR", "sandbox", "integration", "contract", "stub", "isolation"],
        model_answer_hint="Approaches: mock the HTTP client (unit test—fast but may miss real behavior), record/replay (VCR/Betamax—capture real responses), sandbox environments (provider test accounts), contract tests (verify format). Best practice: mock for unit, recorded responses for integration, periodic live tests against sandbox.",
    ),
    Question(
        id="test_022", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is code coverage and what are its limitations?",
        expected_keywords=["coverage", "percentage", "line", "branch", "limitation", "quality", "false confidence", "metric", "untested"],
        model_answer_hint="Code coverage measures what percentage of code is executed by tests. Types: line, branch, path. Limitations: high coverage != good tests (can run code without asserting), doesn't test edge cases, doesn't verify behavior, can give false confidence. Use as a guide, not a goal. Mutation testing better measures test quality.",
    ),
    Question(
        id="test_023", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test concurrent and multi-threaded code?",
        expected_keywords=["concurrent", "race condition", "thread", "deterministic", "stress", "synchronization", "deadlock", "latch", "barrier"],
        model_answer_hint="Challenges: non-deterministic, hard to reproduce bugs. Approaches: stress testing (many threads, many iterations), use latches/barriers to control timing, thread sanitizers (TSAN), deterministic scheduling (force specific interleavings), property-based testing with concurrent scenarios. Test for: race conditions, deadlocks, data corruption.",
    ),
    Question(
        id="test_024", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="What is mutation testing and how does it improve test quality?",
        expected_keywords=["mutation", "mutant", "kill", "survive", "quality", "assertion", "fault", "pitest", "strength"],
        model_answer_hint="Mutation testing introduces small changes (mutants) to production code and checks if tests catch them (kill). Surviving mutants = missing test cases. Measures test suite strength better than coverage. Mutants: change operators (+→-), conditions (> → >=), remove statements. Tools: Pitest (Java), mutmut (Python). Computationally expensive but reveals weak tests.",
    ),
    Question(
        id="test_025", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test event-driven architectures?",
        expected_keywords=["event", "async", "eventually", "consumer", "producer", "message", "integration", "ordering", "idempotent"],
        model_answer_hint="Test levels: unit test event handlers (mock message bus), integration test with embedded broker (testcontainers), end-to-end with real broker. Verify: events published correctly, consumers handle events (including retries), ordering, idempotency. Use awaitility/polling for eventually-consistent assertions. Test dead letter handling.",
    ),
    Question(
        id="test_026", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What is the Arrange-Act-Assert pattern?",
        expected_keywords=["arrange", "act", "assert", "setup", "execute", "verify", "readable", "structure", "given-when-then"],
        model_answer_hint="AAA structures tests clearly: Arrange (set up test data, mocks, preconditions), Act (execute the behavior under test), Assert (verify expected outcomes). Also known as Given-When-Then in BDD. Benefits: readable, consistent, easy to identify what failed. One Act per test for clarity.",
    ),
    Question(
        id="test_027", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test API performance and set SLOs?",
        expected_keywords=["SLO", "latency", "percentile", "p99", "throughput", "baseline", "regression", "benchmark", "budget"],
        model_answer_hint="Define SLOs: p50/p95/p99 latency targets, throughput requirements, error rate budget. Implement: baseline benchmarks in CI, catch performance regressions automatically, load test regularly (k6/Locust). Track: latency percentiles (not averages), throughput under load, resource utilization. Alert on SLO violation in production.",
    ),
    Question(
        id="test_028", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you implement end-to-end testing that is reliable in CI?",
        expected_keywords=["e2e", "reliable", "flaky", "retry", "wait", "isolation", "seed data", "cleanup", "deterministic", "container"],
        model_answer_hint="Reliability strategies: explicit waits (not sleep), retry flaky operations, isolated test data (unique per run), deterministic seed data, containerized dependencies, reset state between tests, parallel-safe tests. Avoid: shared state, time-dependent tests, network-dependent external calls. Use test IDs for cleanup. Keep e2e suite small and focused on critical paths.",
    ),
    Question(
        id="test_029", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="What is BDD (Behavior-Driven Development) and how does it differ from TDD?",
        expected_keywords=["BDD", "behavior", "Given-When-Then", "Gherkin", "Cucumber", "specification", "stakeholder", "acceptance", "readable"],
        model_answer_hint="BDD extends TDD by writing tests in natural language (Given-When-Then/Gherkin). Focus: behavior from user perspective, not implementation. Stakeholders can read/write specs. Tools: Cucumber, Behave. Differs from TDD: higher-level (acceptance vs unit), natural language, stakeholder collaboration. Both are test-first approaches.",
    ),
    Question(
        id="test_030", topic="testing_advanced", difficulty="medium", category="testing",
        question_type="technical",
        text="How do you test security vulnerabilities in your application?",
        expected_keywords=["SAST", "DAST", "penetration", "OWASP", "dependency scanning", "fuzz", "security testing", "automated", "vulnerability"],
        model_answer_hint="Automated: SAST (static analysis—Semgrep, CodeQL), DAST (dynamic—OWASP ZAP, Burp Suite), dependency scanning (Snyk, Dependabot), fuzz testing. Manual: penetration testing, security code review. In CI: SAST + dependency scanning on every PR. Regular: penetration tests quarterly. Test OWASP Top 10 scenarios.",
    ),
    Question(
        id="test_031", topic="testing_basics", difficulty="easy", category="testing",
        question_type="technical",
        text="What are test fixtures and how do you manage them?",
        expected_keywords=["fixture", "setup", "teardown", "reusable", "data", "state", "scope", "factory", "before/after"],
        model_answer_hint="Fixtures: reusable setup/teardown logic for tests. Provide: test data, configured objects, external resource connections. Scope: per-test (isolated), per-class, per-module. In pytest: @pytest.fixture with yield for cleanup. Factories (factory_boy) for flexible data creation. Keep fixtures simple and composable.",
    ),
    Question(
        id="test_032", topic="testing_advanced", difficulty="hard", category="testing",
        question_type="technical",
        text="How do you test machine learning models?",
        expected_keywords=["ML testing", "data validation", "model performance", "regression", "bias", "distribution", "training-serving skew", "monitoring"],
        model_answer_hint="ML testing layers: data validation (schema, distributions, missing values), model performance (metrics above threshold, no regression from previous version), fairness/bias testing across groups, training-serving skew detection, integration tests (end-to-end prediction pipeline), A/B testing in production. Use: Great Expectations for data, MLflow for model comparison.",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL SECURITY QUESTIONS (17)
# ═══════════════════════════════════════════════════════════════════════════════

SECURITY_EXTRA_QUESTIONS = [
    Question(
        id="sec_016", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is the principle of least privilege and how do you apply it?",
        expected_keywords=["least privilege", "minimal", "access", "need-to-know", "permission", "role", "restrict", "audit"],
        model_answer_hint="Least privilege: grant only minimum permissions needed for a task. Application: restrict file permissions, use limited DB accounts for apps, IAM roles with specific actions, run processes as non-root, time-limited access, regular access reviews. Defense in depth—limits blast radius of compromise.",
    ),
    Question(
        id="sec_017", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is input validation and why is it crucial for security?",
        expected_keywords=["input validation", "whitelist", "sanitize", "reject", "server-side", "injection", "boundary", "type check"],
        model_answer_hint="Input validation: verify all user input matches expected format/type/range before processing. Always server-side (client-side is UX only). Approaches: whitelist (accept known good) preferred over blacklist. Validate: type, length, format, range, encoding. Prevents: injection attacks, buffer overflows, logic flaws.",
    ),
    Question(
        id="sec_018", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you implement secure session management?",
        expected_keywords=["session", "cookie", "HttpOnly", "Secure", "SameSite", "expiration", "regenerate", "invalidate", "HTTPS"],
        model_answer_hint="Secure sessions: HttpOnly cookies (prevent XSS access), Secure flag (HTTPS only), SameSite attribute (CSRF protection), short expiration, regenerate session ID on login (prevent fixation), invalidate on logout, encrypt session data, use server-side sessions over client-side for sensitive data.",
    ),
    Question(
        id="sec_019", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="What are common cryptographic mistakes developers make?",
        expected_keywords=["crypto", "homebrew", "MD5", "SHA1", "ECB", "hardcoded key", "random", "deprecated", "salt"],
        model_answer_hint="Common mistakes: rolling your own crypto, using deprecated algorithms (MD5, SHA1 for security), ECB mode (patterns visible), hardcoded keys/secrets, weak random number generation (Math.random instead of crypto), not using authenticated encryption (AES-GCM), no salt for password hashing, reusing IVs/nonces.",
    ),
    Question(
        id="sec_020", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you protect against supply chain attacks?",
        expected_keywords=["supply chain", "dependency", "lockfile", "SCA", "signing", "SBOM", "pin", "audit", "verified"],
        model_answer_hint="Protections: lock dependencies (lockfiles), audit packages (npm audit, pip-audit), pin versions, use SCA tools (Snyk, Dependabot), verify package signatures, generate SBOM, use private registry/proxy, review new dependencies before adding, monitor for compromised packages, minimal dependencies principle.",
    ),
    Question(
        id="sec_021", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you implement end-to-end encryption in a messaging application?",
        expected_keywords=["E2E", "asymmetric", "key exchange", "Diffie-Hellman", "Signal Protocol", "forward secrecy", "key management", "ratchet"],
        model_answer_hint="Signal Protocol approach: Double Ratchet algorithm for forward secrecy. Key exchange: X3DH (Extended Triple Diffie-Hellman). Each message uses unique key (ratcheting). Server never has plaintext. Challenges: key management (device registration), multi-device sync, group messaging, key verification (safety numbers).",
    ),
    Question(
        id="sec_022", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="What is SSRF (Server-Side Request Forgery) and how do you prevent it?",
        expected_keywords=["SSRF", "server-side", "request", "internal", "metadata", "whitelist", "validate URL", "network segmentation"],
        model_answer_hint="SSRF: attacker tricks server into making requests to internal resources (metadata services, internal APIs, localhost). Prevention: whitelist allowed URLs/domains, validate and sanitize URLs, block internal IP ranges, use network segmentation, disable unnecessary protocols (file://, gopher://), cloud metadata endpoint protection (IMDSv2).",
    ),
    Question(
        id="sec_023", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is defense in depth and how do you apply it?",
        expected_keywords=["defense in depth", "layers", "multiple", "controls", "fail", "redundancy", "security", "firewall", "encryption"],
        model_answer_hint="Defense in depth: multiple layers of security so that if one fails, others still protect. Layers: network (firewall, WAF), transport (TLS), application (input validation, auth), data (encryption at rest), monitoring (detection and response). No single control is sufficient.",
    ),
    Question(
        id="sec_024", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you design a secrets rotation strategy?",
        expected_keywords=["rotation", "secrets", "automated", "zero-downtime", "vault", "TTL", "lease", "dynamic", "graceful"],
        model_answer_hint="Strategy: automated rotation on schedule (30-90 days), zero-downtime rotation (support old+new during transition period), dynamic secrets (short-lived, generated on-demand via Vault), alert on rotation failures, test rotation in staging. Tools: HashiCorp Vault, AWS Secrets Manager. Pattern: generate new → deploy → verify → revoke old.",
    ),
    Question(
        id="sec_025", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you secure a REST API against common attacks?",
        expected_keywords=["rate limiting", "authentication", "HTTPS", "input validation", "CORS", "headers", "WAF", "logging", "injection"],
        model_answer_hint="API security checklist: HTTPS everywhere, strong authentication (OAuth2/JWT), rate limiting, input validation (every endpoint), proper CORS configuration, security headers (HSTS, X-Content-Type-Options), SQL/NoSQL injection prevention, request size limits, logging/monitoring suspicious activity, WAF for additional protection.",
    ),
    Question(
        id="sec_026", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="What is threat modeling and how do you perform it?",
        expected_keywords=["threat model", "STRIDE", "attack surface", "data flow", "asset", "mitigation", "risk", "diagram", "boundary"],
        model_answer_hint="Threat modeling process: 1) Identify assets and entry points, 2) Create data flow diagrams with trust boundaries, 3) Identify threats using STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege), 4) Rate risk (likelihood x impact), 5) Define mitigations. Do early in design phase, update regularly.",
    ),
    Question(
        id="sec_027", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you secure containers and container images?",
        expected_keywords=["scan", "base image", "non-root", "read-only", "vulnerabilities", "signing", "runtime", "minimal", "Trivy"],
        model_answer_hint="Image security: minimal base images (distroless, alpine), scan for vulnerabilities (Trivy, Snyk Container), sign images (cosign), pin base image digests. Runtime: run as non-root, read-only filesystem, drop capabilities, no privileged mode, resource limits. Registry: private, access control, scan on push.",
    ),
    Question(
        id="sec_028", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What are security headers and which ones should every web app implement?",
        expected_keywords=["HSTS", "X-Content-Type-Options", "X-Frame-Options", "CSP", "security header", "browser", "Referrer-Policy"],
        model_answer_hint="Essential headers: Strict-Transport-Security (force HTTPS), X-Content-Type-Options: nosniff (prevent MIME sniffing), X-Frame-Options: DENY (prevent clickjacking), Content-Security-Policy (control resource loading), Referrer-Policy (limit referrer info), Permissions-Policy (restrict browser features). Set on all responses.",
    ),
    Question(
        id="sec_029", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you implement secure multi-tenancy in a SaaS application?",
        expected_keywords=["multi-tenant", "isolation", "data leakage", "RLS", "tenant context", "encryption", "testing", "noisy neighbor"],
        model_answer_hint="Isolation levels: shared DB with Row-Level Security (RLS), schema-per-tenant, DB-per-tenant. Always validate tenant context on every request. Encrypt tenant data with per-tenant keys. Test: cross-tenant data leakage tests, tenant impersonation. Prevent noisy neighbor (resource quotas). Audit access.",
    ),
    Question(
        id="sec_030", topic="security_advanced", difficulty="medium", category="security",
        question_type="technical",
        text="How do you securely handle file uploads?",
        expected_keywords=["upload", "validation", "type check", "size limit", "malware", "rename", "storage", "path traversal", "sandbox"],
        model_answer_hint="Secure uploads: validate file type (magic bytes, not just extension), enforce size limits, rename files (prevent path traversal), store outside webroot, scan for malware, use separate storage service (S3), serve through CDN (not directly), set Content-Disposition header, limit upload rate, virus scan.",
    ),
    Question(
        id="sec_031", topic="security_advanced", difficulty="hard", category="security",
        question_type="technical",
        text="How do you design an audit logging system for compliance?",
        expected_keywords=["audit log", "immutable", "tamper-proof", "who-what-when", "retention", "compliance", "structured", "alerting", "GDPR"],
        model_answer_hint="Audit log design: capture who (user/service), what (action, resource, old/new values), when (timestamp), where (IP, device). Requirements: immutable (append-only, write-once storage), tamper-evident (hash chains), structured format, retention policies (compliance-driven), access controls on logs, real-time alerting on suspicious patterns.",
    ),
    Question(
        id="sec_032", topic="security_basics", difficulty="easy", category="security",
        question_type="technical",
        text="What is multi-factor authentication and why is it important?",
        expected_keywords=["MFA", "2FA", "factor", "something you know", "something you have", "TOTP", "phishing", "security"],
        model_answer_hint="MFA requires 2+ verification factors: something you know (password), something you have (phone/hardware key), something you are (biometric). Dramatically reduces account compromise from stolen passwords/phishing. Methods: TOTP apps, hardware keys (FIDO2/WebAuthn—phishing resistant), SMS (weakest). Always offer, require for sensitive operations.",
    ),
]




# ═══════════════════════════════════════════════════════════════════════════════
# QUESTION BANK CLASS
# ═══════════════════════════════════════════════════════════════════════════════


class QuestionBank:
    """Manages the complete question database with search and filtering."""

    def __init__(self):
        self._questions: Dict[str, Question] = {}
        self._by_category: Dict[str, List[Question]] = {}
        self._by_difficulty: Dict[str, List[Question]] = {}
        self._by_type: Dict[str, List[Question]] = {}
        self._load_all_questions()

    def _load_all_questions(self):
        """Load all question sets into indexed structures."""
        all_questions = (
            PYTHON_QUESTIONS +
            JAVASCRIPT_QUESTIONS +
            REACT_QUESTIONS +
            SQL_QUESTIONS +
            AWS_QUESTIONS +
            DOCKER_QUESTIONS +
            ML_QUESTIONS +
            SYSTEM_DESIGN_QUESTIONS +
            DSA_QUESTIONS +
            API_QUESTIONS +
            GIT_QUESTIONS +
            TESTING_QUESTIONS +
            SECURITY_QUESTIONS +
            BEHAVIORAL_QUESTIONS +
            DOCKER_EXTRA_QUESTIONS +
            API_EXTRA_QUESTIONS +
            GIT_EXTRA_QUESTIONS +
            TESTING_EXTRA_QUESTIONS +
            SECURITY_EXTRA_QUESTIONS
        )

        for q in all_questions:
            self._questions[q.id] = q

            # Index by category
            if q.category not in self._by_category:
                self._by_category[q.category] = []
            self._by_category[q.category].append(q)

            # Index by difficulty
            if q.difficulty not in self._by_difficulty:
                self._by_difficulty[q.difficulty] = []
            self._by_difficulty[q.difficulty].append(q)

            # Index by type
            if q.question_type not in self._by_type:
                self._by_type[q.question_type] = []
            self._by_type[q.question_type].append(q)

    @property
    def total_questions(self) -> int:
        """Total number of questions in the bank."""
        return len(self._questions)

    @property
    def categories(self) -> List[str]:
        """List of available categories."""
        return sorted(self._by_category.keys())

    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID."""
        return self._questions.get(question_id)

    def get_by_category(self, category: str) -> List[Question]:
        """Get all questions in a category."""
        return self._by_category.get(category, [])

    def get_by_difficulty(self, difficulty: str) -> List[Question]:
        """Get all questions of a specific difficulty."""
        return self._by_difficulty.get(difficulty, [])

    def get_by_type(self, question_type: str) -> List[Question]:
        """Get all questions of a specific type (technical/hr)."""
        return self._by_type.get(question_type, [])

    def filter_questions(
        self,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        question_type: Optional[str] = None,
    ) -> List[Question]:
        """Filter questions by multiple criteria."""
        results = list(self._questions.values())

        if categories:
            results = [q for q in results if q.category in categories]
        if difficulties:
            results = [q for q in results if q.difficulty in difficulties]
        if question_type:
            results = [q for q in results if q.question_type == question_type]

        return results

    def random_selection(
        self,
        n: int = 10,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        question_type: Optional[str] = None,
        ensure_variety: bool = True,
    ) -> List[Question]:
        """Select random questions with optional variety enforcement."""
        pool = self.filter_questions(categories, difficulties, question_type)

        if not pool:
            return []

        if not ensure_variety or n >= len(pool):
            return random.sample(pool, min(n, len(pool)))

        # Ensure variety across categories
        selected = []
        category_pools: Dict[str, List[Question]] = {}
        for q in pool:
            if q.category not in category_pools:
                category_pools[q.category] = []
            category_pools[q.category].append(q)

        # Round-robin selection from each category
        category_keys = list(category_pools.keys())
        random.shuffle(category_keys)

        while len(selected) < n:
            added_this_round = False
            for cat in category_keys:
                if len(selected) >= n:
                    break
                cat_pool = category_pools[cat]
                if cat_pool:
                    choice = random.choice(cat_pool)
                    cat_pool.remove(choice)
                    selected.append(choice)
                    added_this_round = True

            if not added_this_round:
                break  # No more questions available

        return selected

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about the question bank."""
        stats = {
            "total": self.total_questions,
            "by_category": {cat: len(qs) for cat, qs in self._by_category.items()},
            "by_difficulty": {diff: len(qs) for diff, qs in self._by_difficulty.items()},
            "by_type": {t: len(qs) for t, qs in self._by_type.items()},
        }
        return stats


# Module-level singleton for convenience
_default_bank: Optional[QuestionBank] = None


def get_question_bank() -> QuestionBank:
    """Get the default question bank singleton."""
    global _default_bank
    if _default_bank is None:
        _default_bank = QuestionBank()
    return _default_bank
