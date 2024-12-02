//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`ProtocolException`����C++���Ѿ����ڡ�


/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/auth/AuthenticationException.java,v 1.6 2004/05/13 04:02:00 mbecke Exp $
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

#include "ProtocolException.h"  // ����ProtocolException�Ѿ�ʵ��

/**
 * Signals a failure in authentication process
 *
 * @author <a href="mailto:oleg@ural.ru">Oleg Kalnichevski</a>
 * 
 * @since 2.0
 */
class AuthenticationException : public ProtocolException {

public:
    /**
     * Creates a new AuthenticationException with a <tt>null</tt> detail message. 
     */
    AuthenticationException() : ProtocolException() {}

    /**
     * Creates a new AuthenticationException with the specified message.
     * 
     * @param message the exception detail message
     */
    AuthenticationException(const std::string& message) : ProtocolException(message) {}

    /**
     * Creates a new AuthenticationException with the specified detail message and cause.
     * 
     * @param message the exception detail message
     * @param cause the <tt>Throwable</tt> that caused this exception, or <tt>null</tt>
     * if the cause is unavailable, unknown, or not a <tt>Throwable</tt>
     * 
     * @since 3.0
     */
    AuthenticationException(const std::string& message, const std::exception* cause) 
        : ProtocolException(message, cause) {}

};


// ### ˵����
// 1. **�̳й�ϵ**����C++�У�`AuthenticationException`��̳���`ProtocolException`�࣬����Java�еļ̳й�ϵһ�¡�
// 2. **���캯��**��C++�еĹ��캯����Java�еĹ��캯��������ͬ��ֻ���﷨���в�ͬ��
// 3. **�쳣����**����C++�У��쳣����ͨ��ʹ��`std::exception`���������ࡣ�������`ProtocolException`�Ѿ�ʵ�������Ƶ��쳣�������ơ�
// 4. **������**������`ProtocolException`���Ѿ�ʵ�֣����Ұ����ʵ��Ĺ��캯���ͳ�Ա������

// ��ȷ����ʵ��ʹ��ʱ��`ProtocolException`���Ѿ���ȷʵ�֣����Ұ�����Java�汾����ͬ�Ĺ��캯���ͳ�Ա������