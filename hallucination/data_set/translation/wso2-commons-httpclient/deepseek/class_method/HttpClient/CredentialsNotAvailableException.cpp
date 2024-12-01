//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`AuthenticationException`����C++���Ѿ����塣

//```cpp
/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/auth/CredentialsNotAvailableException.java,v 1.4 2004/05/13 04:02:00 mbecke Exp $
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

#include <stdexcept>
#include <string>

class AuthenticationException : public std::runtime_error {
public:
    AuthenticationException() : std::runtime_error("Authentication Exception") {}
    AuthenticationException(const std::string& message) : std::runtime_error(message) {}
    AuthenticationException(const std::string& message, const std::exception& cause) : std::runtime_error(message) {}
};

/**
 * Authentication credentials required to respond to a authentication 
 * challenge are not available
 *
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 3.0
 */
class CredentialsNotAvailableException : public AuthenticationException {
public:
    /**
     * Creates a new CredentialsNotAvailableException with a <tt>null</tt> detail message. 
     */
    CredentialsNotAvailableException() : AuthenticationException() {}

    /**
     * Creates a new CredentialsNotAvailableException with the specified message.
     * 
     * @param message the exception detail message
     */
    CredentialsNotAvailableException(const std::string& message) : AuthenticationException(message) {}

    /**
     * Creates a new CredentialsNotAvailableException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>Throwable</tt> that caused this exception, or <tt>null</tt>
     * if the cause is unavailable, unknown, or not a <tt>Throwable</tt>
     */
    CredentialsNotAvailableException(const std::string& message, const std::exception& cause) : AuthenticationException(message) {}
};
// ```

// ### ˵����
// 1. **�̳й�ϵ**����C++�У�`CredentialsNotAvailableException`�̳���`AuthenticationException`����`AuthenticationException`�̳���`std::runtime_error`��
// 2. **���캯��**��C++�еĹ��캯����Java�еĹ��캯�����ƣ����﷨���в�ͬ��
// 3. **�쳣����**��C++�е��쳣����ʹ��`std::exception`���������࣬����Java�е�`Throwable`�����ơ�

// ### �����
// - `AuthenticationException`����Ҫ��C++���Ѿ����壬���Ҽ̳���`std::runtime_error`��
// - `std::string`��`std::exception`��C++��׼���һ���֣��������ʵ�֡�