// �����ǽ�Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`DefaultHttpParams`�ࡣ

// ```cpp
#include <string>
#include "DefaultHttpParams.h"  // ����DefaultHttpParams���Ѿ�ʵ��

class HttpConnectionParams : public DefaultHttpParams {
public:
    static const std::string SO_TIMEOUT;
    static const std::string TCP_NODELAY;
    static const std::string SO_SNDBUF;
    static const std::string SO_RCVBUF;
    static const std::string SO_LINGER;
    static const std::string CONNECTION_TIMEOUT;
    static const std::string STALE_CONNECTION_CHECK;

    HttpConnectionParams() : DefaultHttpParams() {}

    int getSoTimeout() const {
        return getIntParameter(SO_TIMEOUT, 0);
    }

    void setSoTimeout(int timeout) {
        setIntParameter(SO_TIMEOUT, timeout);
    }

    void setTcpNoDelay(bool value) {
        setBooleanParameter(TCP_NODELAY, value);
    }

    bool getTcpNoDelay() const {
        return getBooleanParameter(TCP_NODELAY, true);
    }

    int getSendBufferSize() const {
        return getIntParameter(SO_SNDBUF, -1);
    }

    void setSendBufferSize(int size) {
        setIntParameter(SO_SNDBUF, size);
    }

    int getReceiveBufferSize() const {
        return getIntParameter(SO_RCVBUF, -1);
    }

    void setReceiveBufferSize(int size) {
        setIntParameter(SO_RCVBUF, size);
    }

    int getLinger() const {
        return getIntParameter(SO_LINGER, -1);
    }

    void setLinger(int value) {
        setIntParameter(SO_LINGER, value);
    }

    int getConnectionTimeout() const {
        return getIntParameter(CONNECTION_TIMEOUT, 0);
    }

    void setConnectionTimeout(int timeout) {
        setIntParameter(CONNECTION_TIMEOUT, timeout);
    }

    bool isStaleCheckingEnabled() const {
        return getBooleanParameter(STALE_CONNECTION_CHECK, true);
    }

    void setStaleCheckingEnabled(bool value) {
        setBooleanParameter(STALE_CONNECTION_CHECK, value);
    }
};

const std::string HttpConnectionParams::SO_TIMEOUT = "http.socket.timeout";
const std::string HttpConnectionParams::TCP_NODELAY = "http.tcp.nodelay";
const std::string HttpConnectionParams::SO_SNDBUF = "http.socket.sendbuffer";
const std::string HttpConnectionParams::SO_RCVBUF = "http.socket.receivebuffer";
const std::string HttpConnectionParams::SO_LINGER = "http.socket.linger";
const std::string HttpConnectionParams::CONNECTION_TIMEOUT = "http.connection.timeout";
const std::string HttpConnectionParams::STALE_CONNECTION_CHECK = "http.connection.stalecheck";
// ```

// ### ˵����
// 1. **��������**��Java�е�`public static final`�ַ���������C++�б�ת��Ϊ`static const std::string`��
// 2. **����ʵ��**��Java�еķ�����ת��ΪC++�еĳ�Ա������ע�⣬C++�еĳ�Ա����Ĭ����`inline`�ģ���˲���Ҫ��ʽ������
// 3. **�̳�**��`HttpConnectionParams`��̳���`DefaultHttpParams`������Java�еļ̳�һ�¡�
// 4. **����ת��**��Java�е�`Integer`��`Boolean`������C++�зֱ��Ӧ`int`��`bool`��
// 5. **���캯��**��C++�еĹ��캯����Java�еĹ��캯�����ƣ���ʼ�����ಿ��ͨ��`DefaultHttpParams()`��ɡ�

// ### �����
// - `DefaultHttpParams`����Ҫʵ��`getIntParameter`��`setIntParameter`��`getBooleanParameter`��`setBooleanParameter`��������Щ������Java�����б����á�

// ### ע�����
// - ȷ��`DefaultHttpParams`���ʵ����Java�汾һ�£��Ա���ȷ���������Ļ�ȡ�����á�
// - C++�е��ַ���ʹ��`std::string`��������Java�е�`String`�ࡣ