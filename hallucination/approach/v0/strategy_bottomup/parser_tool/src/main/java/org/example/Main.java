package org.example;

import com.github.javaparser.JavaParser;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.comments.Comment;
import com.github.javaparser.printer.DefaultPrettyPrinter;
import com.github.javaparser.ast.stmt.BlockStmt;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class Main {

    public static void main(String[] args) throws Exception {
        String fileDirPath = "D:\\projects\\sitp\\sitp-dataset\\translation_java-cpp";
        File dir = new File(fileDirPath);
        File[] projects = dir.listFiles();
        if (projects != null) {
            for (File project : projects) {
                if (project.getName().equals("output_info")) {
                    continue;
                }
                String projectName = project.getName();
                File sourcerFilesDir = new File(fileDirPath + "\\" + projectName + "\\source");
                File[] sourceFiles = sourcerFilesDir.listFiles();
                if (sourceFiles != null)
                    for (File file : sourceFiles) {
                        String fileName = file.getName().split("\\.")[0];
                        forOneFileNew(
                                fileDirPath + "\\" + projectName + "\\source\\" + fileName
                                        + ".java",
                                fileDirPath + "\\" + projectName + "\\split\\" + fileName
                                        + ".txt");
                    }
                else {
                    System.out.println("file to open:" + sourcerFilesDir.getName());
                }
            }
        }
    }

    public static void forOneFileNew(String inputFile, String outputFile) {
        try {
            // 解析输入文件
            FileInputStream in = new FileInputStream(inputFile);
            JavaParser javaParser = new JavaParser();
            CompilationUnit cu = javaParser.parse(in).getResult().orElse(null);
            if (cu == null) {
                System.out.println("failed to parse the file " + inputFile);
                return;
            }

            // 处理编译单元中的所有类型声明
            boolean multyWarning = false;
            for (TypeDeclaration<?> decl : cu.findAll(TypeDeclaration.class)) {
                if (!decl.isNestedType()) {
                    if (multyWarning) {
                        System.out.println("warning: multiple classes found in " + inputFile);
                        break;
                    }
                    // 方法体
                    ArrayList<String> methodBodies = new ArrayList<>();
                    String type = removeMethodBody(decl, methodBodies);
                    decl.getAllContainedComments().forEach(Comment::remove);
                    // 输出结果
                    try (FileWriter writer = new FileWriter(outputFile)) {
                        // 输出类声明
                        writer.write("'''" + type + "\n");
                        writer.write("classname:" + decl.getNameAsString() + "\n");
                        DefaultPrettyPrinter printer = new DefaultPrettyPrinter();
                        writer.write(printer.print(decl) + "\n''' \n");

                        // 输出方法体
                        for (String methodBody : methodBodies) {
                            writer.write(methodBody);
                        }
                        System.out.println("Processed file saved to: " + outputFile);
                    }
                    multyWarning = true;
                }
            }
        } catch (IOException e) {
            System.err.println("Error processing file: " + e.getMessage());
        }
    }

    public static String removeMethodBody(TypeDeclaration<?> typeDecl, ArrayList<String> methods) {
        return removeMethodBody(typeDecl, methods, new ArrayList<>());
    }

    private static String removeMethodBody(TypeDeclaration<?> typeDecl,
            ArrayList<String> methods,
            ArrayList<String> outers) {
        String res;
        boolean logMethods;

        if (typeDecl instanceof ClassOrInterfaceDeclaration cofDecl) {
            logMethods = !cofDecl.isInterface();
            res = cofDecl.isInterface() ? "interface" : "class";
        } else if (typeDecl instanceof EnumDeclaration) {
            logMethods = true;
            System.out.println("warning: enum found in " + typeDecl.getNameAsString());
            res = "enum";
        } else {
            System.out.println("warning: unknown type in " + typeDecl.getNameAsString());
            return "unknown";
        }

        // 1) 组装 外类$内类$... 形式的类名
        ArrayList<String> chain = new ArrayList<>(outers);
        chain.add(typeDecl.getNameAsString());
        String classNameDollar = String.join("$", chain);

        typeDecl.getMembers().forEach(member -> {
            if (member instanceof MethodDeclaration method) {
                if (method.getBody().isPresent()) {
                    if (logMethods) {
                        String methodName = method.getNameAsString();
                        String parameters = method.getParameters().stream()
                                .map(p -> p.getType().asString())
                                .reduce((a, b) -> a + "," + b).orElse("");
                        String sig = String.format(
                                "'''method\n//methodname:%s::%s(%s)\n%s\n''' \n",
                                classNameDollar, methodName, parameters, method);
                        methods.add(sig);
                    }
                    method.setBody(null);
                }
            } else if (member instanceof ConstructorDeclaration ctor) {
                if (logMethods) {
                    String parameters = ctor.getParameters().stream()
                            .map(p -> p.getType().asString())
                            .reduce((a, b) -> a + "," + b).orElse("");
                    // 2) 构造：函数名强制为 外类$内类
                    String sig = String.format(
                            "'''method\n//methodname:%s::%s(%s)\n%s\n''' \n",
                            classNameDollar, classNameDollar, parameters, ctor);
                    methods.add(sig);
                }
                ctor.setBody(StaticJavaParser.parseBlock("{}"));
            } else if (member instanceof TypeDeclaration) {
                // 3) 递归内部类，链路继续传下去
                removeMethodBody((TypeDeclaration<?>) member, methods, chain);
            }
        });

        return res;
    }

}
