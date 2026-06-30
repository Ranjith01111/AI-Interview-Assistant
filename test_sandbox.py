import asyncio
from backend.services.sandbox_service import SandboxService

async def main():
    service = SandboxService()
    print('Testing JS')
    js_code = "console.log(require('fs').readFileSync(0, 'utf-8').trim() + ' js');"
    res = await service._execute_local('javascript', js_code, [{'input': 'hello', 'expected_output': 'hello js'}], 2, 128)
    print(res)

    print('Testing Java')
    java_code = 'import java.util.Scanner; public class Solution { public static void main(String[] args) { Scanner s = new Scanner(System.in); System.out.println(s.nextLine() + " java"); } }'
    res = await service._execute_local('java', java_code, [{'input': 'hello', 'expected_output': 'hello java'}], 2, 128)
    print(res)
    
    print('Testing C')
    c_code = '#include <stdio.h>\nint main() { printf("c\\n"); return 0; }'
    res = await service._execute_local('c', c_code, [{'input': '', 'expected_output': 'c'}], 2, 128)
    print(res)
    
    print('Testing CPP')
    cpp_code = '#include <iostream>\nint main() { std::cout << "cpp\\n"; return 0; }'
    res = await service._execute_local('cpp', cpp_code, [{'input': '', 'expected_output': 'cpp'}], 2, 128)
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
