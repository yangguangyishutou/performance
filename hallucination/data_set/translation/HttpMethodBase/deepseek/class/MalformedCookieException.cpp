以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，例如`ProtocolException`类在C++中已经存在。

```cpp
/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/cookie/MalformedCookieException.java,v 1.8 2004/05/13 04:02:00 mbecke Exp $
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

#include "ProtocolException.h"  // 假设ProtocolException类已经实现

/**
 * Signals that a cookie is in some way invalid or illegal in a given
 * context
 *
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 2.0
 */
class MalformedCookieException : public ProtocolException {
public:
    /**
     * Creates a new MalformedCookieException with a <tt>null</tt> detail message.
     */
    MalformedCookieException() : ProtocolException() {}
     
    /** 
     * Creates a new MalformedCookieException with a specified message string.
     * 
     * @param message The exception detail message
     */
    MalformedCookieException(const std::string& message) : ProtocolException(message) {}

    /**
     * Creates a new MalformedCookieException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>std::exception</tt> that caused this exception, or <tt>nullptr</tt>
     * if the cause is unavailable, unknown, or not a <tt>std::exception</tt>
     * 
     * @since 3.0
     */
    MalformedCookieException(const std::string& message, const std::exception* cause) 
        : ProtocolException(message, cause) {}
};
```

### 说明：
1. **继承关系**：在C++中，`MalformedCookieException`类继承自`ProtocolException`类，这与Java中的继承关系一致。
2. **构造函数**：C++中的构造函数与Java中的构造函数功能相同，只是语法略有不同。
3. **异常处理**：在C++中，异常处理通常使用`std::exception`类及其派生类。这里假设`ProtocolException`类已经实现了类似的功能。
4. **依赖项**：假设`ProtocolException`类已经实现，并且包含适当的构造函数和成员函数。

### 注意事项：
- 在C++中，异常处理通常使用`std::exception`类及其派生类。这里假设`ProtocolException`类已经实现了类似的功能。
- 如果`ProtocolException`类没有实现相应的构造函数，你可能需要根据实际情况进行调整。