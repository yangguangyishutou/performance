import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt.cot_examples import *


CFG_prompt = '''
Your task is to construct a simplified Control Flow Graph (CFG) for each version and then detect backward incompatibilities by comparing the two CFGs. Please strictly follow the detailed steps in the `Analysis Phases` section below to identify all incompatibility types and provide concise reasons for the python API provided in the `Source Code` section. The final output should be in the following JSON format:
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

    You must reason using the following conceptual objects.

    **Node**
        Each executable line corresponds to a Node.
        - id: unique
        - content: stripped source line
        - type: one of entry, stmt, return, raise, break, continue, end
        - next: list of outgoing edges. Each edge is (target_node, condition_or_null)

    **Condition**
        A Condition represents a control predicate.
        - type: if, elif, else, while, for, try, except
        - content: full condition text (colon removed)
        - parent_node: list of Nodes that enter this condition

    **Condition Stack (CS)**
        A stack that tracks currently active conditions.


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




##### **Phase 2: CFG Construction (Single Pass, Indentation Driven)**  

Process the function body **line by line**, ignoring empty lines.

Initialize:

* `current = ENTRY`
* `CS = empty ConditionStack`
* `indent_stack = [0]`
* `cond_indent_stack = []`
* `last_stmt_masked = False`

---

###### Step 1: Indentation Reduction (Scope Exit)

Before processing a line:

While `current_indent < indent_stack[-1]`:

1. Pop `indent_stack`
2. If `cond_indent_stack[-1] >= current_indent`:

   * Pop `cond_indent_stack`
   * Pop one condition from `CS`
   * Record it as `last_cond` (used for backfilling exits)

This step represents **fully exiting a conditional block**.

---

###### If statement is a condition:

For Condition Start Statements: (`if`, `while`, `for`, `try`)

    1. Create a new `Condition`:
        * `parent_node = [current]`
        * `content = line without trailing ':'`
    2. Push condition into `CS`
    3. Record its indentation in `cond_indent_stack`
    4. Push indentation into `indent_stack`
    5. **Do not create a Node**
    6. Continue to next line

For Condition Middle Statements: (`elif`, `else`, `except`)

    1. If `last_cond` exists:
        * `parent_node = last_cond.parent_node + [current]`
        * If the previous statement was masked, exclude `current`
        * Reset `current` to `last_cond.parent_node[0]`
    2. Create a new `Condition` with the computed parents
    3. Push condition into `CS`
    4. Push indentation into both stacks
    5. **Do not create a Node**
    6. Continue to next line

---

###### If statement is an Ordinary Statement:

For all other lines:
1. Create a `Node` of type `stmt`
2. Add it to CFG

If a condition block just ended (`last_cond` exists):
1. For every node `p` in `last_cond.parent_node`:
2. * Add edge: `p → current_node` (no condition)

Let `indent` be current indentation.

Case A: Indentation Increases (Entering Condition Body)

* If `CS.top()` exists:
  * Add edge: `current → node` with condition = `CS.top()`
  * Push indentation

Case B: Same Indentation, Condition Active

* If previous statement was **not masked**:
  * Add edge: `current → node` (unconditional)
* If masked:
  * This node is implicitly masked as well

Case C: Indentation Ends

* Add edge: `current → node` (unconditional)

---

###### Special Statements

Masked statements:

If `return`, `raise`, `break`, `continue`
    * mask the following same indent statements(unreachable)

End statements:
* If `return` or `raise`:
  * Add edge: `node → END`

---

###### Finalization

After all lines:

1. Pop all remaining conditions in `CS`
2. For each parent node of those conditions:
   * Add edge to `END`
3. If `current` is not `END`, connect `current → END`

---

##### Phase 3: Source–Sink Labeling (During CFG Construction)

While constructing the CFG, Use the following data structure to record important nodes:

* Parameter assignments and uses. For instance, PA_amount1 represents all nodes in CFG1 for code_v1 that contains an assignment to parameter `amount`
* Global variable assignments. Similar to Parameter but you have to decide which one is Global variable.
* Return nodes. For instance, R1 represents all nodes in CFG1 for code_v1 that contains a `Return` Statement.
* Exception nodes. Similar to Return.
* Nodes present in only one CFG version. For instance, OnlyV1 represents all nodes in CFG1 for code_v1 that doesn't exist in CFG2.

---

##### **Phase 4: Initial Incompatibility Analysis (CI1 and CI4)**  
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

---

##### **Phase 5: Comprehensive Incompatibility Analysis**  
Use data structures to identify the following incompatibilities and update Results:

1. **CI2 (Key of kwargs Addition or Deletion)**: 
KWARGS is NOT empty (both P1 and P2 have `**kwargs`):
    - For each nodes labeled in PU_kwargs1: record all keys accessed by `kwargs.get()` or `kwargs[]`
    - For each nodes labeled in PU_kwargs1: record all keys accessed by `kwargs.get()` or `kwargs[]`
    - If keys of PU_kwargs1 and PU_kwargs1 are different, mark as CI2

2. **CI3 (Parameter Rename)**: 
There exist `(p1, p2)` in `ReName` and Usage of the parameters are highly similar(e.g., same code patterns or usage contexts).
Following situations can be considered highly similar:
    - For each nodes labeled in PA_p1 and PU_p1: record all Usage of the parameter
    - Do the same for p2
    - The assignments to p1 and p2 are identical and most usages are indentical

Exclusions: Do NOT trigger CI3 for:
    - Parameter additions or deletions (these are covered by CI1).
    - Parameter default value changes (these are covered by CI4).


3. **CI5 (Parameter Range Change for exception)**:
CI5 denotes compatibility issues caused by changes of exception conditions which includes any parameter in parameter list. For example, under range A of parameter `p` old code meets the condition to trigger exception E1. However, under the same range of `p`, new code not neccessarily triggers exception E1. If identifing following situation, mark CI5:
    - For exception nodes in E1 and E2:
    1. nodes amounts are different and the added/deleted exception `e` is associated with condition `c` which contains a parameter `p` (`p` must in condition description of `c`).
    2. Or for any pair of exception (`e1` in E1 and `e2` in E2): backtrace the condition c1 for e1 and c2 for e2 through CFG. If both condition contain a parameter `p` but have different range criteria for `p`.

Exclusion: Do NOT trigger CI5 for:
    - the changes of condition statements cause other behavior changes(eg. return different value) other than explicitly raising exception.
    - the changes of condition statements are only related to global variable instead of any parameter.

    
4. **CI6 (Different Exception Thrown)**: 
CI6 denotes compatibility issues caused by changes in exceptions type and exception added or deleted. If identifing following situation, mark CI6:
    - For exception nodes in E1 and E2:
    1. nodes amounts are different which means there exsits added/deleted exception statements `e`.
    2. Or there exists a pair of exception nodes(`e1` in E1 and `e2` in E2): e1 and e2 have different exception type.
    - Or there exists a pair of exception nodes(`e1` in E1 and `e2` in E2): e1 and e2 have different condition but conditions are both irrelated to fuction inputs(eg: parameters).
    
Exclusion: Do NOT trigger CI6 for:
    - Exception message change or warning to warning change.(Message won't affect upper code, only exception type may be caught, so we only need to pay attention to exception type and condition)
    - Condition differ while it is related to function inputs.

5. **CI7 (Return Value Change)**: 
For each return node in R1, if:
it is not in R2, OR trace back for each return node through CFG, and find the data flow of the return variable differs.

Following situations can be considered as different data flows:
    - the data flow difference necessarily changes return value content/type/structure (e.g., dependent variables shift from na_sentinel to use_na_sentinel with actual value impact), excluding "different processing logic but same result" (e.g., zip(*vals) vs get_level_values for index extraction).
    - Exclude non-return-related changes (base class init, Callback logic, exception handling) and @overload stubs (no implementation to analyze return values).
    
Exception: Do NOT trigger CI7 for:
    - No specific return value in both version(eg: No return statements or Only return None).
    - Exception should not be considered as Return Behavior.

6. **CI8 (Global Variable Change)**: Find labeled nodes of global variables. add 'CI8' and reason to Results if control flow or data flow differ and may lead to different value assignments to global variables.

7. **CI9 (Reference Parameter Change)**: Find labeled nodes of reference parameter. Add 'CI9' and reason to Results if At least one of the following changes occurs:
    - Direct assignment to the reference parameter itself: The reference parameter (e.g., self, a custom reference variable) is directly reassigned to a new value (e.g. custom_ref = updated_obj in CFG2 vs. custom_ref = initial_obj in CFG1).
    - Addition of new attributes reassigned to the reference parameter: A new attribute is added to the reference parameter in one version but not the other (e.g., self.new_attr = value exists in CFG2 but not in CFG1; custom_ref.extra_field = data in CFG2 with no such attribute in CFG1).
    - Assignment to existing attributes of the reference parameter: An existing attribute of the reference parameter has different assignment logic or dependent variables (e.g., self.old_attr = a + b in CFG1 vs. self.old_attr = a * b in CFG2).
    
Exception: Do NOT trigger CI9 for:
    - Data flow of Reference Parameter which is used to assign other type of variable should not be considered.
    - The reference parameter(eg: self) is accessed differently instead of being assigned differently
    - Adds new attribute access patterns Or different method calls on self


### Source Code
"code_v1": 
{old_code}

"code_v2": 
{new_code}
'''