-- Direct SQL seed for coding challenges
-- Run: psql -U postgres -p 5433 -d interview_assistant -f scripts/seed_challenges_direct.sql

-- Create table if not exists
CREATE TABLE IF NOT EXISTS coding_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(50) NOT NULL DEFAULT 'Medium',
    template_code JSONB NOT NULL DEFAULT '{}',
    test_cases JSONB NOT NULL DEFAULT '[]',
    time_limit FLOAT NOT NULL DEFAULT 2.0,
    memory_limit INTEGER NOT NULL DEFAULT 128,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Clear existing (avoid duplicates)
DELETE FROM coding_submissions WHERE challenge_id IN (SELECT id FROM coding_challenges);
DELETE FROM coding_challenges;

-- Insert 5 challenges
INSERT INTO coding_challenges (id, title, difficulty, description, template_code, test_cases, time_limit, memory_limit) VALUES
(gen_random_uuid(), 'Two Sum', 'Easy',
 '## Two Sum\n\nGiven an array of integers and a target number, find two numbers that add up to the target.\n\nReturn their indices (0-based).\n\n### Examples\n| Input | Output |\n|-------|--------|\n| 9, [2 7 11 15] | 0 1 |\n| 6, [3 2 4] | 1 2 |',
 '{"python": "import sys\n\ndef solve():\n    lines = sys.stdin.read().splitlines()\n    target = int(lines[0].strip())\n    nums = [int(x) for x in lines[1].strip().split()]\n    # Your solution here\n    pass\n\nif __name__ == ''__main__'':\n    solve()", "javascript": "const lines = require(''fs'').readFileSync(''/dev/stdin'',''utf8'').trim().split(''\\n'');\nconst target = parseInt(lines[0]);\nconst nums = lines[1].split('' '').map(Number);\n// Your solution here"}',
 '[{"input": "9\n2 7 11 15", "expected_output": "0 1", "is_hidden": false}, {"input": "6\n3 2 4", "expected_output": "1 2", "is_hidden": false}, {"input": "6\n3 3", "expected_output": "0 1", "is_hidden": false}]',
 2.0, 128),

(gen_random_uuid(), 'Palindrome Check', 'Easy',
 '## Palindrome Check\n\nGiven a string, determine if it is a palindrome considering only alphanumeric characters and ignoring case.\n\n### Examples\n| Input | Output |\n|-------|--------|\n| A man a plan a canal Panama | true |\n| hello | false |',
 '{"python": "import sys\n\ndef solve():\n    s = sys.stdin.read().strip()\n    # Check if palindrome\n    pass\n\nif __name__ == ''__main__'':\n    solve()", "javascript": "const s = require(''fs'').readFileSync(''/dev/stdin'',''utf8'').trim();\n// Your solution here"}',
 '[{"input": "A man a plan a canal Panama", "expected_output": "true", "is_hidden": false}, {"input": "hello", "expected_output": "false", "is_hidden": false}, {"input": "race a car", "expected_output": "false", "is_hidden": false}]',
 2.0, 128),

(gen_random_uuid(), 'Max Subarray Sum', 'Medium',
 '## Maximum Subarray Sum (Kadane''s Algorithm)\n\nGiven an array of integers, find the contiguous subarray with the largest sum.\n\n### Examples\n| Input | Output |\n|-------|--------|\n| 5, [-2 1 -3 4 -1] | 4 |\n| 4, [1 2 3 4] | 10 |',
 '{"python": "import sys\n\ndef solve():\n    lines = sys.stdin.read().splitlines()\n    n = int(lines[0].strip())\n    nums = [int(x) for x in lines[1].strip().split()]\n    # Kadane''s algorithm here\n    pass\n\nif __name__ == ''__main__'':\n    solve()", "javascript": "const lines = require(''fs'').readFileSync(''/dev/stdin'',''utf8'').trim().split(''\\n'');\nconst n = parseInt(lines[0]);\nconst nums = lines[1].split('' '').map(Number);\n// Your solution here"}',
 '[{"input": "5\n-2 1 -3 4 -1", "expected_output": "4", "is_hidden": false}, {"input": "4\n1 2 3 4", "expected_output": "10", "is_hidden": false}, {"input": "3\n-1 -2 -3", "expected_output": "-1", "is_hidden": false}]',
 2.0, 128),

(gen_random_uuid(), 'Flatten Nested Array', 'Medium',
 '## Flatten Nested Array\n\nGiven a nested array/list, flatten it into a single-level array.\n\n### Examples\n| Input | Output |\n|-------|--------|\n| [1,[2,[3,4],5]] | 1 2 3 4 5 |\n| [[1,2],[3,[4,5]]] | 1 2 3 4 5 |',
 '{"python": "import sys, json\n\ndef solve():\n    data = json.loads(sys.stdin.read().strip())\n    # Flatten the nested list\n    pass\n\nif __name__ == ''__main__'':\n    solve()", "javascript": "const data = JSON.parse(require(''fs'').readFileSync(''/dev/stdin'',''utf8'').trim());\n// Flatten and print space-separated"}',
 '[{"input": "[1,[2,[3,4],5]]", "expected_output": "1 2 3 4 5", "is_hidden": false}, {"input": "[[1,2],[3,[4,5]]]", "expected_output": "1 2 3 4 5", "is_hidden": false}]',
 2.0, 128),

(gen_random_uuid(), 'Employee Department Query', 'Medium',
 '## Employee Department Query (SQL)\n\nWrite a SQL query to find employees who earn more than the average salary in their department.\n\nReturn: employee_name, department, salary',
 '{"sql": "-- Write your SQL query here\nSELECT employee_name, department, salary\nFROM employees\nWHERE salary > (\n    -- subquery for avg salary per department\n);"}',
 '[{"schema_sql": "CREATE TABLE employees (id INTEGER PRIMARY KEY, employee_name TEXT, department TEXT, salary REAL);", "seed_sql": "INSERT INTO employees VALUES (1,''Alice'',''Engineering'',95000),(2,''Bob'',''Engineering'',85000),(3,''Carol'',''Sales'',70000),(4,''Dave'',''Sales'',60000),(5,''Eve'',''Engineering'',100000);", "expected_output": "[{\"employee_name\":\"Alice\",\"department\":\"Engineering\",\"salary\":95000.0},{\"employee_name\":\"Eve\",\"department\":\"Engineering\",\"salary\":100000.0},{\"employee_name\":\"Carol\",\"department\":\"Sales\",\"salary\":70000.0}]", "is_hidden": false}]',
 5.0, 128);

-- Verify
SELECT title, difficulty FROM coding_challenges ORDER BY difficulty, title;
