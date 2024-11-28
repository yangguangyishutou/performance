//�����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����C++���Ѿ���������Ӧ�Ľӿں��ࡣ


/*
 * $Header: /home/jerenkrantz/tmp/commons/commons-convert/cvs/home/cvs/jakarta-commons//httpclient/src/java/org/apache/commons/httpclient/Credentials.java,v 1.9 2004/04/18 23:51:34 jsdever Exp $
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

#ifndef CREDENTIALS_H
#define CREDENTIALS_H

namespace org {
namespace apache {
namespace commons {
namespace httpclient {

/**
 * <p>Authentication credentials.</p>
 * <p>
 * This is just a marker interface, the current implementation has no methods.
 * </p>
 * @author Unascribed
 * @author <a href="mailto:mbowler@GargoyleSoftware.com">Mike Bowler</a>
 * 
 * @version $Revision: 480424 $ $Date: 2006-11-29 06:56:49 +0100 (Wed, 29 Nov 2006) $
 */
class Credentials {
public:
    virtual ~Credentials() = default;
};

} // namespace httpclient
} // namespace commons
} // namespace apache
} // namespace org

#endif // CREDENTIALS_H
// ```

// ### ˵����
// 1. **�����ռ�**��Ϊ�˱�����Java���ṹ��һ���ԣ�ʹ����Ƕ�׵������ռ� `org::apache::commons::httpclient`��
// 2. **�ӿ�ת��Ϊ������**����C++�У��ӿ�ͨ��ͨ����������ʵ�֡����ﶨ����һ����Ϊ `Credentials` �ĳ����࣬����û�ж����κδ��麯������Ϊ��ֻ��һ����ǽӿڡ�
// 3. **��������**��������һ����������������ȷ����ɾ�����������ʱ��ȷ���������������������
// 4. **ͷ�ļ�����**��ʹ�� `#ifndef`, `#define`, `#endif` ����ֹͷ�ļ�����ΰ�����

// ���C++���뱣������ԭʼJava������ͬ�Ĺ��ܺͽṹ��ͬʱ����C++�ı�̹淶��