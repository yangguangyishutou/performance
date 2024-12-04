
/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/auth/AuthChallengeException.java,v 1.2 2004/04/18 23:51:36 jsdever Exp $
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

#include <string>
#include <stdexcept>

// Assuming AuthenticationException is already defined in C++
class AuthenticationException : public std::runtime_error {
public:
    AuthenticationException(const std::string& message) : std::runtime_error(message) {}
    AuthenticationException(const std::string& message, const std::exception& cause) 
        : std::runtime_error(message), cause_(cause) {}

private:
    const std::exception& cause_;
};

/**
 * Signals a failure processing authentication challenge
 *
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 3.0
 */
class AuthChallengeException : public AuthenticationException {
public:
    /**
     * Creates a new AuthChallengeException with a <tt>null</tt> detail message. 
     */
    AuthChallengeException() : AuthenticationException("") {}

    /**
     * Creates a new AuthChallengeException with the specified message.
     * 
     * @param message the exception detail message
     */
    AuthChallengeException(const std::string& message) : AuthenticationException(message) {}

    /**
     * Creates a new AuthChallengeException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>std::exception</tt> that caused this exception, or <tt>nullptr</tt>
     * if the cause is unavailable, unknown, or not a <tt>std::exception</tt>
     */
    AuthChallengeException(const std::string& message, const std::exception& cause) 
        : AuthenticationException(message, cause) {}
};


// ### ˵����
// 1. **�̳й�ϵ**����C++�У�`AuthChallengeException`�̳���`AuthenticationException`����`AuthenticationException`�̳���`std::runtime_error`��
// 2. **���캯��**��C++�еĹ��캯����Java�еĹ��캯�����ƣ����﷨���в�ͬ��
// 3. **�쳣����**��C++�е��쳣����ʹ��`std::exception`���������࣬����Java�е�`Throwable`���ơ�
// 4. **�ַ�������**��C++��ʹ��`std::string`�������ַ���������Java�е�`String`���ơ�

// ### �����
// - ����`AuthenticationException`���Ѿ���C++�ж��壬���Ҽ̳���`std::runtime_error`��
// - ����`std::exception`������ع����Ѿ������ڱ�׼���С�