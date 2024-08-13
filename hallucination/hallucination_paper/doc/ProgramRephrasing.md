- **160**: 根据关键词搜索，找到160处包含equivalent的地方：

- **26 过滤

  - **1. 实际语义为not equivalent (12)**

    - **x = (x \* y) \* z; //** *not equivalent to* **x \*= y \* z;**

    - **z = (x - y) + y ; //** *not equivalent to* **z = x;**

    - **z = x + x \* y; //** *not equivalent to* **z=x\* (1.0 + y);**

    - **y=x/ 5.0; //** *not equivalent to* **y=x\* 0.2;**

  - - 

  - **3. 阐述某个语法的含义 （5）**

    - Incrementing is equivalent to adding 1.)
    - Decrementing is equivalent to subtracting 1.
    - A *compound assignment* of the form **E1** *op* **= E2** is equivalent to the simple assignment expression **E1 = E1** *op* **(E2)**,
    - *x*/2 ↔ *x* × 0.5*12

  - **4. 阐述非代码的功能 （4）**

    - Thus, preprocessing directives are commonly called ‘‘lines’’. These ‘‘lines’’ hav e no other syntactic significance, as all white space is equivalent except in certain situations during preprocessing (see the **#** character string literal creation operator in 6.10.3.2, for example).

    - **f = g/\**//h; //** *equivalent to* **f = g / h;**

    - **/\*//\*/ l(); //** *equivalent to* **l();**

    - **m = n//\**/o**

      **+ p; //** *equivalent to* **m = n + p;**

  - **5. Equivalence in program startup and exit (3) ** 

    - At program startup, the equivalent of **setlocale(LC_ALL, "C");** is executed.
    - int main(void){} ==> int main(int argc, char *argv[]){}

    - If the return type of the **main** function is a type compatible with **int**, a return from the

      initial call to the **main** function is equivalent to calling the **exit** function with the value

      returned by the **main** function as its argument.

- **将这134处分成如下15类：**

  - **1. Logical NOT Expression保留:** !*E* can be rephrased to 0 = *E* and !!*E*  can be rephrased to *E*.(2)

  - **2. Indirection Expression 保留:** ∗&*a* and & ∗ *a* can be rephrased to *a*.(2)
  
  - **3.Macros. 保留**(32)
  
    - **#if defined**-->#ifdef
  
    - **#include <inttypes.h>**
  
      **intmax_t strtoimax(const char \* restrict nptr,**
  
      **char \** restrict endptr, int base);**

      **uintmax_t strtoumax(const char \* restrict nptr,**

      **char \** restrict endptr, int base);** ==> The **strtoimax** and **strtoumax** functions are equivalent to the **strtol**, **strtoll**, **strtoul**, and **strtoull** functions, except that the initial portion of the string is converted to **intmax_t** and **uintmax_t** representation, respectively
  
  - **4. Comparison Expression 保留:** *a* >= *b* can be rephrased to *a* >*b*||*a* == *b*.(5)
  
  - **5. 主要表达式(Primary expression) 不常见(12)：**
  
    - ```c++
      //格式是
      
      L"someString" / u"someString"
      
      //会将附近的同类普通字符串或宽字符串合并到一起，如：
      
        "a" "b" L"c"==L"abc"
      
        u"a" "b" u"c"==u"abc"
      ```

    - **数组等价**

    ```c++
    E1[E2] == (*((E1)+(E2)))
        
    //扩展一下:
    E1[E2][E3]==(*(*(E1+E2)+E3))
    ```
  
    - **自增、自减运算符**
  
      ```c++
      ++E==E+=1
      --E==E-=1
      a = b++ + c;=>a=b+c;b=b+1;
      a = ++b + c;=>b=b+1;a=b+c;
      ```
  
    - **二进制去反**
  
      **~E** is equivalent to the maximum value representable in that type minus **E**.
  
  - - 
  
  - **6. Jump statements）不常用**(1)
  
    - ```
      while (/* ... */) {
      
      /* ... */
      
      continue;
      
      /* ... */
      
      contin: ;
      
      }
      
      do {
      
      /* ... */
      
      continue;
      
      /* ... */
      
      contin: ;
      
      } while (/* ... */);
      
      for (/* ... */) {
      
      /* ... */
      
      continue;
      
      /* ... */
      
      contin: ;
      
      }
      
      // 这些continue都等价于 go to contin, 其中contin位于循环体末尾，且其中不包含任何语句
      ```
  
  - **2. Equivalence in Struct (2)**
  
    - Moreover, two structure, union, or enumerated types declared in separate translation units are compatible if their tags and members satisfy the following requirements: If one is declared with a tag, the other shall be declared with the same tag. If both are completed anywhere within their respective translation units, then the following additional requirements apply: there shall be a one-to-one correspondence between their members such that each pair of corresponding members are declared with compatible types; if one member of the pair is declared with an alignment specifier, the other is declared with an equivalent alignment specifier; and if one member of the pair is declared with a name, the other is declared with the same name. For two structures, corresponding members shall be declared in the same order. For two structures or unions, corresponding bit-fields shall have the same widths. For two enumerations, corresponding members shall have the same values.
    - If the definition of an object has an alignment specifier, any other declaration of that object shall either specify equivalent alignment or have no alignment specifier. 
  
  - **7. 函数指针的等价(不常用)**(3+1)
  
    ```c++
    int f(void);
    
    /\* *...* */
    
    g(f);
    
    Then the definition of g might read
    
    void g(int (\*funcp)(void))
    
    {
    
    /\* *...* */
    
    (\*funcp)(); /\* *or* funcp(); *...* */
    
    }
    
    or, equivalently,
    
    void g(int func(void))
    
    {
    
    /\* *...* */
    
    func(); /\* *or* (\*func)(); */
    
    }
    ```
  
    * 指针赋值之后，就相当于重命名
  
  - **8. 不常用的API1**(1)
  
    - //  对齐说明符
  
      _Alignas ( type-name ) == _Alignas(alignof(type-name))

  - **9. Join(不常用API)**(1)
  
    - join(x,y)->x##y

    - otherwise, they are equivalent to calling the corresponding **logb** function and casting the returned value to type **int**.
  
    - Equivalent to **atomic_thread_fence(order)**, except that ‘‘synchronizes with’’
  
      relationships are established only between a thread and a signal handler executed in the
  
      same thread.
  
    - The operation of the **atomic_fetch** and modify generic functions are nearly equivalent to the

      operation of the corresponding *op***=** compound assignment operators. The only differences are that the compound assignment operators are not guaranteed to operate atomically, and the value yielded by a compound assignment operator is the updated value of the object, whereas the value returned by the **atomic_fetch** and modify generic functions is the previous value of the atomic object.
  
  - **10  Manipulation functions**(12)
  
    - cproj(z)==INFINITY + I * copysign(0.0, cimag(z))
    - **nan 方法**（包括四个关键词）
  
    ```c++
    nan("n-char-sequence") == strtod("NAN(n-char-sequence)", (char**) NULL)
    ```
  
    - **nexttoward function**
    - **ctime_s 方法**
  
  - **11 各种输入输出函数之间的转换**(46)
  
    - for example, The **vscanf** function is equivalent to **scanf**, with the variable argument list replaced by **arg**, which shall have been initialized by the **va_start** macro (and possibly subsequent **va_arg** calls). The **vscanf** function does not invoke the **va_end** macro.
  
    - **setbuf funcion**
      - the **setbuf** function is equivalent to the **setvbuf** function invoked with the values **_IOFBF** for **mode** and **BUFSIZ** for **size**, or (if **buf** is a null pointer), with the value **_IONBF** for **mode**.
  
  - **12. Restartable multibyte/wide character conversion functions**(4)
  
    -  If **s** is a null pointer, the **mbrtoc16** function is equivalent to the call: **mbrtoc16(NULL, "", 1, ps)**
    - **c16rtomb** **function** and so on.
  
  - **13. Exponential and logarithmic functions**
  
    - **The** **ldexp** **functions**:On a binary system, **ldexp(x, exp)** is equivalent to **scalbn(x, exp)**.(1)
  
  - **14. Power and absolute value functions**(2)
  
    - **hypot(***x***,** *y***)**, **hypot(***y***,** *x***)**, and **hypot(***x***,** −*y***)** are equivalent.
    - **hypot(***x***,** ±0**)** is equivalent to **fabs(***x***)**.
  
  - **15. Numeric conversion functions**(2)
  
    - The **atoi**, **atol**, and **atoll** functions convert the initial portion of the string pointed to by **nptr** to **int**, **long int**, and **long long int** representation, respectively. Except for the behavior on error, they are equivalent to **atoi: (int)strtol(nptr, (char \**)NULL, 10)**，**atol: strtol(nptr, (char \**)NULL, 10)**， **atoll: strtoll(nptr, (char \**)NULL, 10)**
  
  