以下是将Java代码翻译成C++的版本。假设相关的依赖项已经实现，并且C++中已经定义了相应的类和接口。

```cpp
/*
 * $Header: $
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

#ifndef COOKIE_VERSION_SUPPORT_H
#define COOKIE_VERSION_SUPPORT_H

#include "Header.h"  // 假设Header类已经定义

/**
 * Defines cookie specification specific capabilities
 * 
 * @author <a href="mailto:oleg at ural.ru">Oleg Kalnichevski</a>
 *
 * @since 3.1
 */
class CookieVersionSupport {
public:
    virtual ~CookieVersionSupport() = default;

    virtual int getVersion() const = 0;
    
    virtual Header getVersionHeader() const = 0;
};

#endif // COOKIE_VERSION_SUPPORT_H
```

### 说明：
1. **头文件保护**：使用 `#ifndef`, `#define`, `#endif` 来防止头文件被多次包含。
2. **虚析构函数**：在C++中，接口类通常需要一个虚析构函数，以确保在删除派生类对象时正确调用析构函数。
3. **纯虚函数**：`getVersion` 和 `getVersionHeader` 被定义为纯虚函数，使得 `CookieVersionSupport` 成为一个抽象基类（接口）。
4. **依赖项**：假设 `Header` 类已经在 `Header.h` 中定义，并且已经包含在项目中。

这个C++代码定义了一个接口类 `CookieVersionSupport`，它与原始Java代码中的接口具有相同的功能。