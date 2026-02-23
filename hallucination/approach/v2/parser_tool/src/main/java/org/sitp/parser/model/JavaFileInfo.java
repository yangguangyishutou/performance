package org.sitp.parser.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents extracted information from a Java source file.
 */
public class JavaFileInfo {
    private String filePath;
    private String className;
    private String type;
    private List<String> imports;
    private String classDeclaration;
    private String parentClass;
    private List<String> interfaces;
    private List<String> fieldDeclarations;
    private List<MethodInfo> methods;
    private int methodCount;

    public JavaFileInfo() {
        this.imports = new ArrayList<>();
        this.interfaces = new ArrayList<>();
        this.fieldDeclarations = new ArrayList<>();
        this.methods = new ArrayList<>();
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public List<String> getImports() {
        return imports;
    }

    public void setImports(List<String> imports) {
        this.imports = imports;
    }

    public String getClassDeclaration() {
        return classDeclaration;
    }

    public void setClassDeclaration(String classDeclaration) {
        this.classDeclaration = classDeclaration;
    }

    public String getParentClass() {
        return parentClass;
    }

    public void setParentClass(String parentClass) {
        this.parentClass = parentClass;
    }

    public List<String> getInterfaces() {
        return interfaces;
    }

    public void setInterfaces(List<String> interfaces) {
        this.interfaces = interfaces;
    }

    public List<String> getFieldDeclarations() {
        return fieldDeclarations;
    }

    public void setFieldDeclarations(List<String> fieldDeclarations) {
        this.fieldDeclarations = fieldDeclarations;
    }

    public List<MethodInfo> getMethods() {
        return methods;
    }

    public void setMethods(List<MethodInfo> methods) {
        this.methods = methods;
    }

    public int getMethodCount() {
        return methodCount;
    }

    public void setMethodCount(int methodCount) {
        this.methodCount = methodCount;
    }
}
