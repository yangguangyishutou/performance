//�����ǽ�������Java���뷭���C++�İ汾��������ص��������Ѿ�ʵ�֣�����`HttpParams`��`HttpMethodParams`�ࡣ


#include <string>
#include <vector>
#include <memory>

// ���� HttpParams �� HttpMethodParams �Ѿ�ʵ��
class HttpParams;
class HttpMethodParams;

class HostParams : public HttpParams {
public:
    /**
     * Defines the request headers to be sent per default with each request.
     * <p>
     * This parameter expects a value of type {@link std::vector<std::shared_ptr<Header>>}. The 
     * collection is expected to contain {@link std::shared_ptr<Header>}. 
     * </p>
     */
    static const std::string DEFAULT_HEADERS;

    /**
     * Creates a new collection of parameters with the collection returned
     * by {@link #getDefaultParams()} as a parent. The collection will defer
     * to its parent for a default value if a particular parameter is not 
     * explicitly set in the collection itself.
     * 
     * @see #getDefaultParams()
     */
    HostParams() : HttpParams() {}

    /**
     * Creates a new collection of parameters with the given parent. 
     * The collection will defer to its parent for a default value 
     * if a particular parameter is not explicitly set in the collection
     * itself.
     * 
     * @param defaults the parent collection to defer to, if a parameter
     * is not explictly set in the collection itself.
     *
     * @see #getDefaultParams()
     */
    HostParams(std::shared_ptr<HttpParams> defaults) : HttpParams(defaults) {}
    
    /**
     * Sets the virtual host name.
     * 
     * @param hostname The host name
     */
    void setVirtualHost(const std::string& hostname) {
        setParameter(HttpMethodParams::VIRTUAL_HOST, hostname);
    }

    /**
     * Returns the virtual host name.
     * 
     * @return The virtual host name
     */
    std::string getVirtualHost() const {
        return std::any_cast<std::string>(getParameter(HttpMethodParams::VIRTUAL_HOST));
    }
};

const std::string HostParams::DEFAULT_HEADERS = "http.default-headers";
// ```

// ### ˵����
// 1. **�����ռ���ඨ��**��
//    - `HostParams` ��̳��� `HttpParams` �ࡣ
//    - `DEFAULT_HEADERS` ��һ����̬�����ַ�����������Ĭ�ϵ�����ͷ��

// 2. **���캯��**��
//    - Ĭ�Ϲ��캯�� `HostParams()` �����˸����Ĭ�Ϲ��캯����
//    - �������Ĺ��캯�� `HostParams(std::shared_ptr<HttpParams> defaults)` �����˸���Ĵ��������캯�����������ø��������ϡ�

// 3. **�����������úͻ�ȡ**��
//    - `setVirtualHost(const std::string& hostname)` ������������������������
//    - `getVirtualHost() const` �������ڻ�ȡ������������

// 4. **������**��
//    - ���� `HttpParams` �� `HttpMethodParams` ���Ѿ�ʵ�֣����� `HttpMethodParams::VIRTUAL_HOST` ��һ�������ַ�����
//    - `setParameter` �� `getParameter` ���������Ѿ��� `HttpParams` ����ʵ�֡�

// 5. **����ת��**��
//    - ʹ�� `std::any_cast` ��������ת�������� `getParameter` ���ص��� `std::any` ���͡�

// ### ע�����
// - C++ ��û��ֱ�Ӷ�Ӧ Java �� `Collection` ���ͣ����ʹ���� `std::vector<std::shared_ptr<Header>>` ����ʾ���ϡ�
// - `std::shared_ptr` ���ڹ���������������ڣ������� Java �е��������͡�
// - `std::any` ���ڴ洢�������͵�ֵ�������� Java �е� `Object`��

// ��������������ص��������Ѿ�ʵ�֣�������ѭ�� Java ������߼��͹��ܡ�