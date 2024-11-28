以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`ProtocolException`类在C++中已经定义。

```cpp
/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/auth/MalformedChallengeException.java,v 1.6 2004/05/13 04:02:00 mbecke Exp $
 * $Revision: 480424 $
 * $Date: 2006-11-29 06:56:49 +0100 (Wed, 29 Nov 2006) $
 *
 * ====================================================================
 *
 *  Licensed to the Apache Software Foundation (ASF) under one or more
 *  contributor license agreements.  See the NOTICE file distributed with
 *  this work for additional information regarding copyright ownership.
 *  The ASF licenses this file to You under the Apache License, Version 2.0
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 * ====================================================================
 *
 * This software consists of voluntary contributions made by many
 * individuals on behalf of the Apache Software Foundation.  For more
 * information on the Apache Software Foundation, please see
 * <http://www.apache.org/>.
 *
 */

#include "ProtocolException.h"  // 假设ProtocolException类已经定义

/**
 * Signals that authentication challenge is in some way invalid or 
 * illegal in the given context
 *
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 2.0
 */
class MalformedChallengeException : public ProtocolException {
public:
    /**
     * Creates a new MalformedChallengeException with a <tt>null</tt> detail message. 
     */
    MalformedChallengeException() : ProtocolException() {}

    /**
     * Creates a new MalformedChallengeException with the specified message.
     * 
     * @param message the exception detail message
     */
    MalformedChallengeException(const std::string& message) : ProtocolException(message) {}

    /**
     * Creates a new MalformedChallengeException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>std::exception</tt> that caused this exception, or <tt>nullptr</tt>
     * if the cause is unavailable, unknown, or not a <tt>std::exception</tt>
     * 
     * @since 3.0
     */
    MalformedChallengeException(const std::string& message, const std::exception* cause) 
        : ProtocolException(message, cause) {}
};
```

### 说明：
1. **继承关系**：在C++中，`MalformedChallengeException`类继承自`ProtocolException`类。
2. **构造函数**：
   - 默认构造函数调用基类的默认构造函数。
   - 带消息的构造函数调用基类的构造函数并传递消息。
   - 带消息和原因的构造函数调用基类的构造函数并传递消息和原因。
3. **异常处理**：在C++中，异常处理通常使用`std::exception`作为基类，因此`cause`参数类型为`const std::exception*`。

### 依赖项：
- 假设`ProtocolException`类已经定义，并且它支持带消息和原因的构造函数。
- 假设`std::string`和`std::exception`在C++标准库中已经定义。