"""
Seed Coding Challenges — Run: python -m backend.seed_challenges
Also callable from startup: await seed_default_challenges(db)

5 Challenges: 3 Programming (Python/Java/C/C++) + 1 JavaScript + 1 SQL
"""

import uuid
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


CHALLENGES = [
    # ═══════════════════════════════════════════════════
    # CHALLENGE 1: Two Sum (Programming - Easy)
    # ═══════════════════════════════════════════════════
    {
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": """## Two Sum

Given an array of integers and a target number, find two numbers that add up to the target.

**Return their indices (0-based).**

### Input
- Line 1: Target integer
- Line 2: Space-separated integers

### Output
- Space-separated indices of the two numbers

### Constraints
- Exactly one valid solution exists
- Cannot use the same element twice

### Examples

| Input | Output |
|-------|--------|
| `9`<br>`2 7 11 15` | `0 1` |
| `6`<br>`3 2 4` | `1 2` |
| `6`<br>`3 3` | `0 1` |
""",
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "python": """import sys

def solve():
    lines = sys.stdin.read().splitlines()
    target = int(lines[0].strip())
    nums = [int(x) for x in lines[1].strip().split()]

    # Your solution here
    # Find two indices i, j such that nums[i] + nums[j] == target
    # Print: i j

    pass

if __name__ == '__main__':
    solve()
""",
            "javascript": """const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');
const target = parseInt(lines[0]);
const nums = lines[1].split(' ').map(Number);

// Your solution here
// Find two indices i, j such that nums[i] + nums[j] == target
// console.log(i + ' ' + j);
""",
            "java": """import java.util.*;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int target = Integer.parseInt(sc.nextLine().trim());
        String[] parts = sc.nextLine().trim().split(" ");
        int[] nums = new int[parts.length];
        for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i]);

        // Your solution here
        // Find two indices i, j such that nums[i] + nums[j] == target
        // System.out.println(i + " " + j);
    }
}
""",
            "c": """#include <stdio.h>
#include <stdlib.h>

int main() {
    int target, n = 0;
    int nums[10000];
    scanf("%d", &target);
    while (scanf("%d", &nums[n]) == 1) n++;

    // Your solution here
    // Find two indices i, j such that nums[i] + nums[j] == target
    // printf("%d %d\\n", i, j);

    return 0;
}
""",
            "cpp": """#include <iostream>
#include <vector>
#include <unordered_map>
using namespace std;

int main() {
    int target, x;
    cin >> target;
    vector<int> nums;
    while (cin >> x) nums.push_back(x);

    // Your solution here
    // Find two indices i, j such that nums[i] + nums[j] == target
    // cout << i << " " << j << endl;

    return 0;
}
""",
        },
        "test_cases": [
            {"input": "9\n2 7 11 15", "expected_output": "0 1", "is_hidden": False},
            {"input": "6\n3 2 4", "expected_output": "1 2", "is_hidden": False},
            {"input": "6\n3 3", "expected_output": "0 1", "is_hidden": False},
            {"input": "10\n1 5 3 7 2", "expected_output": "1 3", "is_hidden": True},
            {"input": "-1\n-3 4 3 90", "expected_output": "0 2", "is_hidden": True},
        ],
    },

    # ═══════════════════════════════════════════════════
    # CHALLENGE 2: Palindrome Check (Programming - Easy)
    # ═══════════════════════════════════════════════════
    {
        "title": "Palindrome Check",
        "difficulty": "Easy",
        "description": """## Palindrome Check

Given a string, determine if it is a palindrome considering only alphanumeric characters and ignoring case.

### Input
- A single line string

### Output
- `true` if palindrome, `false` otherwise

### Examples

| Input | Output |
|-------|--------|
| `A man a plan a canal Panama` | `true` |
| `hello` | `false` |
| `Was it a car or a cat I saw` | `true` |
| `race a car` | `false` |
""",
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "python": """import sys

def solve():
    s = sys.stdin.read().strip()

    # Your solution here
    # Check if s is a palindrome (alphanumeric only, case-insensitive)
    # Print: true or false

    pass

if __name__ == '__main__':
    solve()
""",
            "javascript": """const s = require('fs').readFileSync(0,'utf8').trim();

// Your solution here
// Check if s is a palindrome (alphanumeric only, case-insensitive)
// console.log('true' or 'false');
""",
            "java": """import java.util.*;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().trim();

        // Your solution here
        // Check if s is a palindrome (alphanumeric only, case-insensitive)
        // System.out.println("true" or "false");
    }
}
""",
            "c": """#include <stdio.h>
#include <string.h>
#include <ctype.h>

int main() {
    char s[10000];
    fgets(s, sizeof(s), stdin);

    // Your solution here
    // Check if s is a palindrome (alphanumeric only, case-insensitive)
    // printf("true\\n") or printf("false\\n");

    return 0;
}
""",
            "cpp": """#include <iostream>
#include <string>
#include <algorithm>
using namespace std;

int main() {
    string s;
    getline(cin, s);

    // Your solution here
    // Check if s is a palindrome (alphanumeric only, case-insensitive)
    // cout << "true" or "false" << endl;

    return 0;
}
""",
        },
        "test_cases": [
            {"input": "A man a plan a canal Panama", "expected_output": "true", "is_hidden": False},
            {"input": "hello", "expected_output": "false", "is_hidden": False},
            {"input": "Was it a car or a cat I saw", "expected_output": "true", "is_hidden": False},
            {"input": "race a car", "expected_output": "false", "is_hidden": True},
            {"input": "a", "expected_output": "true", "is_hidden": True},
        ],
    },

    # ═══════════════════════════════════════════════════
    # CHALLENGE 3: Max Subarray Sum (Programming - Medium)
    # ═══════════════════════════════════════════════════
    {
        "title": "Max Subarray Sum",
        "difficulty": "Medium",
        "description": """## Maximum Subarray Sum (Kadane's Algorithm)

Given an array of integers (can include negatives), find the **contiguous subarray** with the largest sum.

Return just the sum.

### Input
- Line 1: Integer N (size of array)
- Line 2: N space-separated integers

### Output
- Single integer: the maximum subarray sum

### Examples

| Input | Output |
|-------|--------|
| `5`<br>`-2 1 -3 4 -1` | `4` |
| `6`<br>`-2 1 -3 4 -1 2` | `5` |
| `3`<br>`-1 -2 -3` | `-1` |
| `4`<br>`1 2 3 4` | `10` |

### Hint
Look up Kadane's Algorithm — O(n) time, O(1) space.
""",
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "python": """import sys

def solve():
    lines = sys.stdin.read().splitlines()
    n = int(lines[0].strip())
    nums = [int(x) for x in lines[1].strip().split()]

    # Your solution here
    # Find the maximum sum of any contiguous subarray
    # Print the sum

    pass

if __name__ == '__main__':
    solve()
""",
            "javascript": """const lines = require('fs').readFileSync(0,'utf8').trim().split('\\n');
const n = parseInt(lines[0]);
const nums = lines[1].split(' ').map(Number);

// Your solution here
// Find maximum contiguous subarray sum
// console.log(maxSum);
""",
            "java": """import java.util.*;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = Integer.parseInt(sc.nextLine().trim());
        String[] parts = sc.nextLine().trim().split(" ");
        int[] nums = new int[n];
        for (int i = 0; i < n; i++) nums[i] = Integer.parseInt(parts[i]);

        // Your solution here — Kadane's Algorithm
        // System.out.println(maxSum);
    }
}
""",
            "c": """#include <stdio.h>

int main() {
    int n, i;
    scanf("%d", &n);
    int nums[n];
    for (i = 0; i < n; i++) scanf("%d", &nums[i]);

    // Your solution here — Kadane's Algorithm
    // printf("%d\\n", maxSum);

    return 0;
}
""",
            "cpp": """#include <iostream>
#include <vector>
#include <climits>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> nums(n);
    for (int i = 0; i < n; i++) cin >> nums[i];

    // Your solution here — Kadane's Algorithm
    // cout << maxSum << endl;

    return 0;
}
""",
        },
        "test_cases": [
            {"input": "5\n-2 1 -3 4 -1", "expected_output": "4", "is_hidden": False},
            {"input": "6\n-2 1 -3 4 -1 2", "expected_output": "5", "is_hidden": False},
            {"input": "3\n-1 -2 -3", "expected_output": "-1", "is_hidden": False},
            {"input": "4\n1 2 3 4", "expected_output": "10", "is_hidden": True},
            {"input": "8\n-1 2 3 -5 4 6 -1 2", "expected_output": "11", "is_hidden": True},
        ],
    },

    # ═══════════════════════════════════════════════════
    # CHALLENGE 4: Array Manipulation (JavaScript Only)
    # ═══════════════════════════════════════════════════
    {
        "title": "Flatten Nested Array",
        "difficulty": "Medium",
        "description": """## Flatten Nested Array (JavaScript)

Given a nested array of integers, flatten it into a single-level array and sort in ascending order.

### Input
- A single line containing a JSON array (can be nested to any depth)

### Output
- A JSON array with all numbers flattened and sorted ascending

### Examples

| Input | Output |
|-------|--------|
| `[1,[2,[3,4],5],6]` | `[1,2,3,4,5,6]` |
| `[[3,2],[1],[4,[5]]]` | `[1,2,3,4,5]` |
| `[10,[5,[1,8]],3]` | `[1,3,5,8,10]` |

### Note
This challenge is designed for JavaScript. Use recursion or `Array.flat(Infinity)`.
""",
        "time_limit": 2.0,
        "memory_limit": 128,
        "template_code": {
            "javascript": """const input = require('fs').readFileSync(0,'utf8').trim();
const arr = JSON.parse(input);

// Your solution here
// Flatten the nested array and sort ascending
// Output as JSON array: console.log(JSON.stringify(result));
""",
            "python": """import sys
import json

def solve():
    data = json.loads(sys.stdin.read().strip())

    # Your solution here
    # Flatten nested list and sort ascending
    # print(json.dumps(result, separators=(',', ':')))

    pass

if __name__ == '__main__':
    solve()
""",
            "java": """import java.util.*;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String input = sc.nextLine().trim();

        // Parse and flatten the nested array, sort ascending
        // Output as JSON array
    }
}
""",
            "c": """#include <stdio.h>
// Note: This challenge is best suited for JavaScript
// C implementation would need manual JSON parsing

int main() {
    // Read input, parse nested array, flatten, sort
    // Print as JSON array
    return 0;
}
""",
            "cpp": """#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;
// Note: This challenge is best suited for JavaScript

int main() {
    // Read input, parse nested array, flatten, sort
    // Print as JSON array
    return 0;
}
""",
        },
        "test_cases": [
            {"input": "[1,[2,[3,4],5],6]", "expected_output": "[1,2,3,4,5,6]", "is_hidden": False},
            {"input": "[[3,2],[1],[4,[5]]]", "expected_output": "[1,2,3,4,5]", "is_hidden": False},
            {"input": "[10,[5,[1,8]],3]", "expected_output": "[1,3,5,8,10]", "is_hidden": False},
            {"input": "[[[[7]]],2,[3,[4,[5,6]]],1]", "expected_output": "[1,2,3,4,5,6,7]", "is_hidden": True},
            {"input": "[100,[50,[25]],[75,[10,5]]]", "expected_output": "[5,10,25,50,75,100]", "is_hidden": True},
        ],
    },

    # ═══════════════════════════════════════════════════
    # CHALLENGE 5: SQL Query (SQL Only)
    # ═══════════════════════════════════════════════════
    {
        "title": "Employee Department Query",
        "difficulty": "Medium",
        "description": """## Employee Department Query (SQL)

You have two tables:

```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department_id INT,
    salary DECIMAL(10,2),
    hire_date DATE
);

CREATE TABLE departments (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);
```

### Task
Write a SQL query to find the **top 3 highest-paid employees** along with their department name.

### Output Columns
`name, department_name, salary`

Order by salary descending. If salaries are equal, order by employee name ascending.

### Sample Data

**employees:**
| id | name | department_id | salary | hire_date |
|----|------|--------------|--------|-----------|
| 1 | Alice | 1 | 95000 | 2020-01-15 |
| 2 | Bob | 2 | 82000 | 2019-06-20 |
| 3 | Carol | 1 | 105000 | 2018-03-10 |
| 4 | Dave | 3 | 78000 | 2021-09-01 |
| 5 | Eve | 2 | 105000 | 2017-11-30 |

**departments:**
| id | name |
|----|------|
| 1 | Engineering |
| 2 | Marketing |
| 3 | Sales |

### Expected Output
```
Carol, Engineering, 105000.00
Eve, Marketing, 105000.00
Alice, Engineering, 95000.00
```
""",
        "time_limit": 5.0,
        "memory_limit": 128,
        "template_code": {
            "sql": """-- Write your SQL query here
-- Find top 3 highest-paid employees with department name
-- Columns: name, department_name, salary
-- Order: salary DESC, name ASC

SELECT
    -- your query here
FROM employees e
JOIN departments d ON e.department_id = d.id
-- complete the query
;
""",
            "python": """# SQL Challenge — write the query as a string
# This will be evaluated against a SQLite database

query = \"\"\"
SELECT
    -- your query here
FROM employees e
JOIN departments d ON e.department_id = d.id
-- complete the query
;
\"\"\"
print(query)
""",
            "javascript": """// SQL Challenge — write the query as a string
const query = `
SELECT
    -- your query here
FROM employees e
JOIN departments d ON e.department_id = d.id
-- complete the query
`;
console.log(query);
""",
            "java": """// SQL Challenge
public class Solution {
    public static void main(String[] args) {
        String query = "SELECT e.name, d.name AS department_name, e.salary " +
            "FROM employees e " +
            "JOIN departments d ON e.department_id = d.id " +
            // Complete the query
            "";
        System.out.println(query);
    }
}
""",
            "c": """// SQL Challenge — not ideal for C, use SQL language
#include <stdio.h>
int main() {
    printf("SELECT e.name, d.name AS department_name, e.salary "
           "FROM employees e "
           "JOIN departments d ON e.department_id = d.id "
           // Complete the query
           );
    return 0;
}
""",
            "cpp": """// SQL Challenge — not ideal for C++, use SQL language
#include <iostream>
using namespace std;
int main() {
    cout << "SELECT e.name, d.name AS department_name, e.salary "
         << "FROM employees e "
         << "JOIN departments d ON e.department_id = d.id "
         // Complete the query
         << endl;
    return 0;
}
""",
        },
        "test_cases": [
            {"input": "SELECT e.name, d.name AS department_name, e.salary FROM employees e JOIN departments d ON e.department_id = d.id ORDER BY e.salary DESC, e.name ASC LIMIT 3;", "expected_output": "Carol,Engineering,105000.00\nEve,Marketing,105000.00\nAlice,Engineering,95000.00", "is_hidden": False},
            {"input": "CHECK_COLUMNS", "expected_output": "name,department_name,salary", "is_hidden": False},
            {"input": "CHECK_JOIN", "expected_output": "JOIN", "is_hidden": False},
            {"input": "CHECK_ORDER", "expected_output": "ORDER BY", "is_hidden": True},
            {"input": "CHECK_LIMIT", "expected_output": "LIMIT 3", "is_hidden": True},
        ],
    },
]


async def seed_default_challenges(db: AsyncSession):
    """Insert challenges if table is empty. Bulletproof — never crashes the app."""
    from backend.models.coding_challenge import CodingChallenge
    from sqlalchemy import text, func
    from sqlalchemy import select as sa_select

    # Step 1: Check if table has data
    try:
        result = await db.execute(sa_select(func.count(CodingChallenge.id)))
        count = result.scalar() or 0
        if count >= len(CHALLENGES):
            return 0
    except Exception as e:
        print(f"⚠️  coding_challenges check failed ({e}) — skipping seed to prevent duplicates")
        return 0

    # Step 2: Insert each challenge
    added = 0
    for ch in CHALLENGES:
        try:
            # Check duplicate by title
            dup = await db.execute(
                sa_select(CodingChallenge.id).where(CodingChallenge.title == ch["title"]).limit(1)
            )
            if dup.scalar_one_or_none() is not None:
                continue
        except Exception:
            continue  # If duplicate check fails, SKIP instead of blindly inserting

        try:
            challenge = CodingChallenge(
                id=uuid.uuid4(),
                title=ch["title"],
                difficulty=ch["difficulty"],
                description=ch["description"],
                time_limit=ch["time_limit"],
                memory_limit=ch["memory_limit"],
                template_code=ch["template_code"],
                test_cases=ch["test_cases"],
            )
            db.add(challenge)
            added += 1
        except Exception as e:
            print(f"⚠️  Failed to add '{ch['title']}': {e}")

    # Step 3: Commit
    if added > 0:
        try:
            await db.commit()
        except Exception as e:
            print(f"⚠️  Seed commit failed: {e}")
            await db.rollback()
            return 0
        print(f"✅ Seeded {added} coding challenges")
    return added


# CLI entry point
if __name__ == "__main__":
    from backend.db.session import async_engine, AsyncSessionLocal, init_db
    from backend.db.base import Base

    async def main():
        import backend.models
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            added = await seed_default_challenges(db)
            print(f"\n🎯 Done! {added} challenges added.")

    print("🌱 Seeding coding challenges...")
    asyncio.run(main())
