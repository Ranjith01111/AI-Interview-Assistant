"""
Challenge Seeder — Seeds default coding challenges in the database.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.coding_challenge import CodingChallenge

logger = get_logger("backend.services.challenge_seeder")

CHALLENGES = [
    {
        "id": uuid.UUID("37189196-857e-4b68-b7eb-1bf7386d94a8"),
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": (
            "### Problem Description\n\n"
            "Given an array of integers `nums` and an integer `target`, "
            "return the indices of the two numbers such that they add up to `target`.\n\n"
            "You may assume that each input would have **exactly one solution**, "
            "and you may not use the same element twice.\n\n"
            "### Input Format\n"
            "- **Line 1**: The integer `target`.\n"
            "- **Line 2**: Space-separated list of integers `nums`.\n\n"
            "### Output Format\n"
            "- Print the space-separated index of the two numbers (e.g. `0 1`)."
        ),
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "python": (
                "import sys\n\n"
                "def solve():\n"
                "    # Read stdin\n"
                "    lines = sys.stdin.read().splitlines()\n"
                "    if len(lines) < 2:\n"
                "        return\n"
                "    target = int(lines[0].strip())\n"
                "    nums = [int(x) for x in lines[1].strip().split()]\n\n"
                "    # Write your solution here\n"
                "    pass\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function solve() {\n"
                "    const input = fs.readFileSync(0, 'utf-8').trim().split('\\n');\n"
                "    if (input.length < 2) return;\n"
                "    const target = parseInt(input[0].trim());\n"
                "    const nums = input[1].trim().split(/\\s+/).map(Number);\n\n"
                "    # Write your solution here\n"
                "}\n\n"
                "solve();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <vector>\n"
                "#include <unordered_map>\n\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    int target;\n"
                "    if (!(cin >> target)) return 0;\n"
                "    \n"
                "    int num;\n"
                "    vector<int> nums;\n"
                "    while (cin >> num) {\n"
                "        nums.push_back(num);\n"
                "    }\n\n"
                "    // Write your solution here\n"
                "    return 0;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n"
                "import java.io.*;\n\n"
                "public class Solution {\n"
                "    public static void main(String[] args) throws IOException {\n"
                "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n"
                "        String targetLine = br.readLine();\n"
                "        if (targetLine == null) return;\n"
                "        int target = Integer.parseInt(targetLine.trim());\n"
                "        \n"
                "        String numsLine = br.readLine();\n"
                "        if (numsLine == null) return;\n"
                "        String[] parts = numsLine.trim().split(\"\\\\s+\");\n"
                "        int[] nums = new int[parts.length];\n"
                "        for (int i = 0; i < parts.length; i++) {\n"
                "            nums[i] = Integer.parseInt(parts[i]);\n"
                "        }\n\n"
                "        // Write your solution here\n"
                "    }\n"
                "}\n"
            )
        },
        "test_cases": [
            {
                "input": "9\n2 7 11 15\n",
                "expected_output": "0 1",
                "is_hidden": False
            },
            {
                "input": "6\n3 2 4\n",
                "expected_output": "1 2",
                "is_hidden": False
            },
            {
                "input": "6\n3 3\n",
                "expected_output": "0 1",
                "is_hidden": True
            },
            {
                "input": "10\n1 2 5 8 9\n",
                "expected_output": "1 3",
                "is_hidden": True
            }
        ]
    },
    {
        "id": uuid.UUID("f9a2e6b2-6c39-4402-a7d2-06b23d9b0493"),
        "title": "Longest Palindromic Substring",
        "difficulty": "Medium",
        "description": (
            "### Problem Description\n\n"
            "Given a string `s`, return the **longest palindromic substring** in `s`.\n\n"
            "A palindrome is a string that reads the same backward as forward.\n\n"
            "### Input Format\n"
            "- A single line containing the string `s`.\n\n"
            "### Output Format\n"
            "- Print the longest palindromic substring."
        ),
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "python": (
                "import sys\n\n"
                "def solve():\n"
                "    s = sys.stdin.read().strip()\n"
                "    # Write your solution here\n"
                "    pass\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n"
                "function solve() {\n"
                "    const s = fs.readFileSync(0, 'utf-8').trim();\n"
                "    // Write your solution here\n"
                "}\n"
                "solve();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <string>\n\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    string s;\n"
                "    if (cin >> s) {\n"
                "        // Write your solution here\n"
                "    }\n"
                "    return 0;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n"
                "import java.io.*;\n\n"
                "public class Solution {\n"
                "    public static void main(String[] args) throws IOException {\n"
                "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n"
                "        String s = br.readLine();\n"
                "        if (s == null) return;\n"
                "        // Write your solution here\n"
                "    }\n"
                "}\n"
            )
        },
        "test_cases": [
            {
                "input": "babad\n",
                "expected_output": "bab",
                "is_hidden": False
            },
            {
                "input": "cbbd\n",
                "expected_output": "bb",
                "is_hidden": False
            },
            {
                "input": "a\n",
                "expected_output": "a",
                "is_hidden": True
            },
            {
                "input": "racecar\n",
                "expected_output": "racecar",
                "is_hidden": True
            }
        ]
    },
    {
        "id": uuid.UUID("1be9efca-db3a-4efd-b94f-a9cb4812efd9"),
        "title": "Department Highest Salary",
        "difficulty": "Medium",
        "description": (
            "### Problem Description\n\n"
            "Write a SQL query to find employees who have the **highest salary** in each of the departments.\n\n"
            "### Database Schema\n\n"
            "**Employee** Table:\n"
            "- `id` (INT, Primary Key)\n"
            "- `name` (VARCHAR)\n"
            "- `salary` (INT)\n"
            "- `departmentId` (INT, ForeignKey to Department.id)\n\n"
            "**Department** Table:\n"
            "- `id` (INT, Primary Key)\n"
            "- `name` (VARCHAR)\n\n"
            "### Output Schema\n"
            "Your query must select columns named exactly:\n"
            "- `Department` (Department name)\n"
            "- `Employee` (Employee name)\n"
            "- `Salary` (Employee salary)\n\n"
            "Rows can be returned in any order."
        ),
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "sql": (
                "-- Write your SQL query here\n"
                "-- Tables: Employee, Department\n"
                "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
                "FROM Employee e\n"
                "JOIN Department d ON e.departmentId = d.id\n"
                "WHERE 1=0; -- Replace with correct query\n"
            )
        },
        "test_cases": [
            {
                "input": "SQL test case 1",
                "schema_sql": (
                    "CREATE TABLE Employee (id INT, name VARCHAR, salary INT, departmentId INT);\n"
                    "CREATE TABLE Department (id INT, name VARCHAR);\n"
                ),
                "seed_sql": (
                    "INSERT INTO Employee VALUES (1, 'Joe', 70000, 1);\n"
                    "INSERT INTO Employee VALUES (2, 'Jim', 90000, 1);\n"
                    "INSERT INTO Employee VALUES (3, 'Henry', 80000, 2);\n"
                    "INSERT INTO Employee VALUES (4, 'Sam', 60000, 2);\n"
                    "INSERT INTO Employee VALUES (5, 'Max', 90000, 1);\n"
                    "INSERT INTO Department VALUES (1, 'IT');\n"
                    "INSERT INTO Department VALUES (2, 'Sales');\n"
                ),
                "expected_output": [
                    {"Department": "IT", "Employee": "Jim", "Salary": 90000},
                    {"Department": "IT", "Employee": "Max", "Salary": 90000},
                    {"Department": "Sales", "Employee": "Henry", "Salary": 80000}
                ],
                "is_hidden": False
            },
            {
                "input": "SQL test case 2",
                "schema_sql": (
                    "CREATE TABLE Employee (id INT, name VARCHAR, salary INT, departmentId INT);\n"
                    "CREATE TABLE Department (id INT, name VARCHAR);\n"
                ),
                "seed_sql": (
                    "INSERT INTO Employee VALUES (1, 'Alice', 100000, 1);\n"
                    "INSERT INTO Employee VALUES (2, 'Bob', 120000, 1);\n"
                    "INSERT INTO Department VALUES (1, 'Engineering');\n"
                ),
                "expected_output": [
                    {"Department": "Engineering", "Employee": "Bob", "Salary": 120000}
                ],
                "is_hidden": True
            }
        ]
    }
]


async def seed_challenges(db: AsyncSession) -> None:
    """Seeds the default challenges if they do not exist."""
    logger.info("checking_coding_challenges_seeding")
    
    for c in CHALLENGES:
        result = await db.execute(
            select(CodingChallenge).where(CodingChallenge.id == c["id"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            challenge = CodingChallenge(
                id=c["id"],
                title=c["title"],
                difficulty=c["difficulty"],
                description=c["description"],
                template_code=c["template_code"],
                test_cases=c["test_cases"],
                time_limit=c["time_limit"],
                memory_limit=c["memory_limit"]
            )
            db.add(challenge)
            logger.info("seeded_coding_challenge", title=c["title"], id=str(c["id"]))
        else:
            # Update description or test cases if modified
            existing.title = c["title"]
            existing.difficulty = c["difficulty"]
            existing.description = c["description"]
            existing.template_code = c["template_code"]
            existing.test_cases = c["test_cases"]
            existing.time_limit = c["time_limit"]
            existing.memory_limit = c["memory_limit"]
            logger.info("updated_coding_challenge", title=c["title"], id=str(c["id"]))

    await db.commit()
    logger.info("coding_challenges_seeding_complete")
