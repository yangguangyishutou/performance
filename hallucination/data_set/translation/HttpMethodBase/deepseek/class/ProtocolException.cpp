以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`HttpException`类已经在C++中定义。

```cpp
/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/ProtocolException.java,v 1.4 2004/05/13 04:03:25 mbecke Exp $
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

#include "HttpException.h"  // 假设HttpException类已经定义

/**
 * Signals that an HTTP protocol violation has occurred.  For example, HttpClient
 * detected a malformed status line or headers, a missing message body, etc.
 * 
 * @author <a href="mailto:laura@lwerner.org">Laura Werner</a>
 * 
 * @since 3.0
 */
class ProtocolException : public HttpException {
public:
    /**
     * Creates a new ProtocolException with a <tt>null</tt> detail message. 
     */
    ProtocolException() : HttpException() {}

    /**
     * Creates a new ProtocolException with the specified detail message.
     * 
     * @param message The exception detail message
     */
    ProtocolException(const std::string& message) : HttpException(message) {}

    /**
     * Creates a new ProtocolException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>Throwable</tt> that caused this exception, or <tt>null</tt>
     * if the cause is unavailable, unknown, or not a <tt>Throwable</tt>
     */
    ProtocolException(const std::string& message, const std::exception& cause) 
        : HttpException(message, cause) {}
};
```

### 说明：
1. **继承关系**：在C++中，`ProtocolException`类继承自`HttpException`类，这与Java中的继承关系相同。
2. **构造函数**：C++中的构造函数与Java中的构造函数类似，只是语法略有不同。C++中的构造函数使用初始化列表来调用基类的构造函数。
3. **异常处理**：在C++中，异常处理通常使用`std::exception`类或其派生类。这里假设`HttpException`类已经实现了类似的功能。
4. **字符串类型**：在C++中，字符串通常使用`std::string`，而不是Java中的`String`。

### 依赖项：
- 假设`HttpException`类已经在C++中定义，并且具有与Java版本相似的构造函数和功能。
- 如果`HttpException`类没有实现，你需要根据Java版本的`HttpException`类来实现相应的C++版本。