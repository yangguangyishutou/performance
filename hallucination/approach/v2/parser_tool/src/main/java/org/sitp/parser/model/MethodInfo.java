package org.sitp.parser.model;

/**
 * Represents method information extracted from Java source code.
 */
public class MethodInfo {
    private String methodName;
    private String methodSignature;
    private String methodComment;
    private String methodBody;
    private int statementCount;

    public MethodInfo() {}

    public MethodInfo(String methodName, String methodSignature, String methodComment, String methodBody) {
        this.methodName = methodName;
        this.methodSignature = methodSignature;
        this.methodComment = methodComment;
        this.methodBody = methodBody;
        this.statementCount = 0;
    }

    public MethodInfo(String methodName, String methodSignature, String methodComment, String methodBody, int statementCount) {
        this.methodName = methodName;
        this.methodSignature = methodSignature;
        this.methodComment = methodComment;
        this.methodBody = methodBody;
        this.statementCount = statementCount;
    }

    public String getMethodName() {
        return methodName;
    }

    public void setMethodName(String methodName) {
        this.methodName = methodName;
    }

    public String getMethodSignature() {
        return methodSignature;
    }

    public void setMethodSignature(String methodSignature) {
        this.methodSignature = methodSignature;
    }

    public String getMethodComment() {
        return methodComment;
    }

    public void setMethodComment(String methodComment) {
        this.methodComment = methodComment;
    }

    public String getMethodBody() {
        return methodBody;
    }

    public void setMethodBody(String methodBody) {
        this.methodBody = methodBody;
    }

    public int getStatementCount() {
        return statementCount;
    }

    public void setStatementCount(int statementCount) {
        this.statementCount = statementCount;
    }
}
