import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt.cot_examples import *

integrated_clean_prompt = '''
Analyze two versions of a Python API function (`code_v1` and `code_v2`) to detect incompatibilities. The output must be in JSON format:  


### Instructions:
Please strictly follow the detailed steps in the `Analysis Phases` section below to identify all incompatibility types and provide concise reasons for the python API provided in the `Source Code` section. The final output should be in the following JSON format:
```json
{{
  "additional_info": "info about important variables or structures used in the analysis",
  "reasons": ["reason for type1", "reason for type2", ...],
  "incompatibility": ["type1", "type2", ...]
}}
```
Output should contain all detected incompatibility types and corresponding reasons and additional information. Reasons must be concise and directly reference the data structures differences.
Some examples are provided in the `Examples` section.

### Analysis Phases:

##### **Phase 0: Initialization**  
    Initialize the output structure:
    **Results**: A dictionary with keys `incompatibility` (list of strings), `reasons` (list of strings) and `additional_info`.

    Initialize the following data structure for `code_v1` and `code_v2` to empty structures:  
    - **K1, K2**: Empty lists for keys extracted from KWARGS.  
    - **ReNUsage1, ReNUsage2**: Empty dictionary mapping each parameter in ReName pairs to a list of related code lines.  
    - **C1, C2**: Empty lists for condition statements (as strings).
    - **D1, D2**: Empty lists for data flow. Each entry is a tuple: `(variable_name, variable_type, list_of_dependent_variables, list_of_condition_indices)`. Variable types include: `local variable`, `global variable`, `reference variable`.  
    - **E1, E2**: Empty lists for explicit exception types, each paired with a list of condition indices.  
    - **R1, R2**: Empty lists for return values, each paired with a list of condition indices.  


##### **Phase 1: Parameter List Processing**  
    Extract the parameter lists of `code_v1` and `code_v2` and output the following data structures:  
    1. **P1 and P2**: Lists of parameters for `code_v1` and `code_v2`. Each parameter is represented as a tuple: `(name, position_index, type, default_value)`. 
        - position_index: The index of the parameter in the function signature, starting from 1.
        - Types include: `positional`, `optional` (with default), `**kwargs`.  
        - Use `-` for no default value.  
        - Do not record type annotation
    2. **KWARGS**: The parameter name if `**param_name` exists in both P1 and P2 (especially `kwargs`).  
        - If `**param_name` exists only in P2 or only in P1, set KWARGS to empty.
    3. **ReName**: A list of parameter pairs `(name1, name2)` where:  
        - `name1` is from P1 and `name2` is from P2.  
        - Both names have strong and similar semantic meaning, OR they have weak semantic meaning but identical `position_index`.  \




##### **Phase 3: Function Body Processing (Line-by-Line with Initialization)**  


Process each line of the function body sequentially for both `code_v1` and `code_v2`. For each line: 
1. **Check current condition scope**: 
Use a stack `CS1` and `CS2` to track active condition statements. Update the stack when entering or exiting a condition scope.
If the condition is not in `C1` or `C2`, add it.
 
2. **If the line is a condition statement** (e.g., `if/while condition:` or `try catch`):  
    - Add the condition string to C1 or C2 with a new index (incrementing from 1).  

3. **If the line is an assignment statement** (e.g., `var = expression`):  
    - Analyze the expression to identify dependent variables (e.g., variables used in the right-hand side).  
    - Determine the variable type: `local variable` if defined locally, `global variable` if accessed from outer scope or noted by 'nonlocal' or 'global'(exclude variable import from lib and variable related to self), `reference variable` (including `self`).  
    - Add an entry to D1 or D2: `(var, variable_type, list_of_dependent_variables, current_condition_indices)`.  
    - If the assignment involves a parameter from ReName, add the code line to ReNUsage for that parameter.  

4. **If the line contains `KWARGS` access** (only consider `kwargs.get('key')` or `kwargs['key']`): 
    - ONLY extract keys that are explicitly accessed via `KWARGS` in the function body—specifically, keys from statements using kwargs.get('key') or kwargs['key'].
    - If `KWARGS` is not empty which means both `P1` and `P2` have `**kwargs`, add the key string to K1 or K2 if not already present.
    - Function parameters in the signature are strictly excluded from K1/K2; these parameters belong to the function's parameter list (processed in Phase 1) and are not considered 'keys from KWARGS'.

5. **If the line is an explicit exception statement** (only consider `raise ExceptionType` and `assert`):  
    - Extract the exception type (e.g., `ExceptionType` from `raise`) and add it to E1 or E2 along with the current condition indices.  
    - return None and other implicit behavior should not considered as exception-like behavior
    - warning and logging should not considered as exception-like behavior
    - try ... except (ErrorType) ...(no raise statement) should not be considered as exception-like behavior
    - try ... except (ErrorType1) raise ErrorType2 ... : Ignore ErrorType1 and Record ErrorType2
    
6. **If the line is a return statement** (e.g., `return value`, `yeild value`):  
    - Add the return value expression to R1 or R2 along with the current condition indices.  

After processing all lines, output the updated K1, K2, ReNUsage, C1, C2, D1, D2, E1, E2, R1, R2.


##### **Phase 2: Initial Incompatibility Analysis (CI1 and CI4)**  
Use data structures P1, P2, KWARGS, ReName from Phase 1 to identify the following incompatibilities and update Results:  

**CI1 (Parameter Addition or Deletion)** and **CI4 (Parameter Default Value Change)**:
The difference occurs in the function signature parameters P1 and P2. Check Following situations:
    - A parameter `p` exists in P1 but not in P2, mark CI1.  
    - A parameter `p` exists in P2 but not in P1 and its type is `positional`, mark CI1.  
    - A parameter `p` exists in P2 but not in P1 and its type is `optional`, and the parameter at `position_index + 1` exists in P2, mark CI1.  
    - A parameter `p` exists both in P1 and P2(same name, can have different position index or different type nanotation) but the default values are different, mark CI4.

Exclusions: Do NOT trigger CI1 and CI4 for:
    - Optional parameters added as the last parameter in P2;
    - Local variables/global variables in the function body;
    - Arguments in Call Statements inside the function body;
    - Type annotation changes of existing parameters;


##### **Phase 4: Comprehensive Incompatibility Analysis**  
Use data structures P1, P2, ReName, K1, K2, ReNUsage, C1, C2, D1, D2, E1, E2, R1, R2 sets to identify the following incompatibilities and update Results:

1. **CI2 (Key of kwargs Addition or Deletion)**: 
KWARGS is NOT empty (both P1 and P2 have `**kwargs`) And K1 (keys from KWARGS in code_v1) and K2 (keys from KWARGS in code_v2) are not identical;
Exclusions: Do NOT trigger CI2 if KWARGS is empty (even if K1/K2 are empty or mismatched).

2. **CI3 (Parameter Rename)**: 
There exist `(p1, p2)` in `ReName` and `ReNUsage[p1]` are highly similar to `ReNUsage[p2]`(e.g., same code patterns or usage contexts).
Following situations can be considered highly similar:
    - Identical code lines in `ReNUsage[p1]` and `ReNUsage[p2]`.
    - Data Flow related with p1 in `D1` and p2 in `D2` differ only in variable names but have the same structure and assignment logic.

Exclusions: Do NOT trigger CI3 for:
    - Parameter additions or deletions (these are covered by CI1).
    - Parameter default value changes (these are covered by CI4).


3. **CI5 (Parameter Range Change for exception)**:
CI5 denotes compatibility issues caused by changes of exception conditions which includes any parameter in parameter list. For example, under range A of parameter `p` old code meets the condition to trigger exception E1. However, under the same range of `p`, new code not neccessarily triggers exception E1. If identifing following situation, mark CI5:
    - len(`E1`) != len(`E2`) and the added/deleted exception `e` is associated with condition `c` which contains a parameter `p` (`p` must in condition description of `c`).
    - len(`E1`) = len(`E2`) but there exists a pair of exception (`e1` in E1 and `e2` in E2): e1 has condition c1 containing `p` and e2 has condition c2 also containing `p`. More importantly, c1 and c2 have different range criteria for `p`.

Exclusion: Do NOT trigger CI5 for:
    - the changes of condition statements cause other behavior changes(eg. return different value) other than explicitly raising exception.
    - the changes of condition statements are only related to global variable instead of any parameter.

    
4. **CI6 (Different Exception Thrown)**: 
CI6 denotes compatibility issues caused by changes in exceptions type and exception added or deleted. If identifing following situation, mark CI6:
    - len(`E1`) != len(`E2`) which means there exsits added/deleted exception statements `e`.
    - len(`E1`) = len(`E2`) but there exists a pair of exception (`e1` in E1 and `e2` in E2): e1 and e2 have the same condition but different exception type.
    - len(`E1`) = len(`E2`) but there exists a pair of exception (`e1` in E1 and `e2` in E2): e1 and e2 have different condition but conditions are both irrelated to fuction inputs(eg: parameters).
    
Exclusion: Do NOT trigger CI6 for:
    - Exception message change or warning to warning change.(Message won't affect upper code, only exception type may be caught, so we only need to pay attention to exception type and condition)
    - Condition differ while it is related to function inputs.

5. **CI7 (Return Value Change)**: 
For each `(r1, c1)` in R1, if:
`r1` is not in R2, OR the data flow of the return variable in D1 and D2 differs.

Following situations can be considered as different data flows:
    - the data flow difference necessarily changes return value content/type/structure (e.g., dependent variables shift from na_sentinel to use_na_sentinel with actual value impact), excluding "different processing logic but same result" (e.g., zip(*vals) vs get_level_values for index extraction).
    - Exclude non-return-related changes (base class init, Callback logic, exception handling) and @overload stubs (no implementation to analyze return values).
    
Exception: Do NOT trigger CI7 for:
    - No specific return value in both version(eg: No return statements or Only return None).
    - Exception should not be considered as Return Behavior.

6. **CI8 (Global Variable Change)**: Find data flows of global variables (dg1 from D1, dg2 from D2). add 'CI8' and reason to Results if dg1 and dg2 differ and may lead to different value assignments to global variables.

7. **CI9 (Reference Parameter Change)**: Find data flows whose assigned variable type is `reference` (e.g., `self` in D1 and D2). Add 'CI9' and reason to Results if At least one of the following changes occurs:
    - Direct assignment to the reference parameter itself: The reference parameter (e.g., self, a custom reference variable) is directly reassigned to a new value (e.g. custom_ref = updated_obj in D2 vs. custom_ref = initial_obj in D1).
    - Addition of new attributes reassigned to the reference parameter: A new attribute is added to the reference parameter in one version but not the other (e.g., self.new_attr = value exists in D2 but not in D1; custom_ref.extra_field = data in D2 with no such attribute in D1).
    - Assignment to existing attributes of the reference parameter: An existing attribute of the reference parameter has different assignment logic or dependent variables (e.g., self.old_attr = a + b in D1 vs. self.old_attr = a * b in D2).
    
Exception: Do NOT trigger CI9 for:
    - Data flow of Reference Parameter which is used to assign other type of variable should not be considered.
    - The reference parameter(eg: self) is accessed differently instead of being assigned differently
    - Adds new attribute access patterns Or different method calls on self


### Source Code
"code_v1": 
{old_code}

"code_v2": 
{new_code}


### Examples

##### **Example for Constructing Data structure:**  
- `code_v1`:  
```python
def func(self, a, b=1, **kwargs):
    c = 1
    d = e + b
    f = kwargs.get('kk')
    if self.good:
        e = 10
        return c
    else:
        return d
```  
- **P1**: `[('self', 1, 'self', '-'), ('a', 2, 'positional', '-'), ('b', 3, 'optional', 1), ('kwargs', 4, '**kwargs', '-')]`  
- **KWARGS**: `kwargs`  
- **ReName**: `[('b', 'bb')]`  # Assuming `code_v2` has `bb`  
- **K1**: `['kk']`  
- **ReNUsage1**: `{{'b': ['d = e + b']}}`  
- **C1**: `['self.good is True', 'self.good is False']`  
- **D1**: `[('c', 'local variable', [1], []), ('d', 'local variable', ['e', 'b'], []), ('f', 'local variable', ['kwargs', 'kk'], []), ('e', 'global variable', [10], [1])]`  
- **E1**: `[]`  
- **R1**: `[('c', [1]), ('d', [2])]`  

##### **Example of Different Type Incompatibility Detection:**

'''

integrated_clean_prompt_with_examples = integrated_clean_prompt + EX1 #+ EX_CI1 + EX_CI2_1 + EX_CI4 + EX_CI6 + EX_CI7_1

