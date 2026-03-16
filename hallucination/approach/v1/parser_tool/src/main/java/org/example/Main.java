package org.example;

import com.github.javaparser.JavaParser;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.comments.Comment;
// import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.printer.DefaultPrettyPrinter;
// import com.github.javaparser.ast.stmt.BlockStmt;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) throws Exception {
        // 检查命令行参数
        if (args.length < 2) {
            System.out.println("Usage: java -jar parser.jar <project_path> <output_root_path> [ai_name]");
            System.out.println("Example: java -jar parser.jar D:\\projects\\sitp\\translate\\source_projects\\myproject D:\\projects\\sitp\\translate\\output\\v1 deepseek");
            return;
        }
        
        // 解析命令行参数
        String projectPath = args[0];
        String outputPath = args[1];
        // String aiName = args.length > 2 ? args[2] : "deepseek";
        
        // 处理指定的项目
        File project = new File(projectPath);
        if (!project.exists() || !project.isDirectory()) {
            System.out.println("Error: Project path does not exist or is not a directory: " + projectPath);
            return;
        }
        
        String projectName = project.getName();
        File[] sourceFiles = project.listFiles();

        File outputDir = new File(outputPath);
        if (!outputDir.exists()) {
            outputDir.mkdirs(); // 使用mkdirs创建多级目录
        }
        
        if (sourceFiles != null) {
            for (File file : sourceFiles) {
                String[] fileNameParts = file.getName().split("\\.");
                if (fileNameParts.length < 2) {
                    continue;
                }
                String ext = fileNameParts[1];
                if (!ext.equals("java")) {
                    continue;
                }
                String fileName = fileNameParts[0];
                
                forOneFileNew(
                        projectPath + "\\" + fileName + ".java",
                        outputPath + "\\" + fileName + ".txt");
            }
        } else {
            System.out.println("Failed to list files in project: " + projectName);
        }
    }

    public static void forOneFileNew(String inputFile, String outputFile) {
        String parent_dir_path = outputFile.substring(0, outputFile.lastIndexOf("\\"));
        File parent_dir = new File(parent_dir_path);
        if (!parent_dir.exists()) {
            parent_dir.mkdirs();
        }

        // 检查输入文件是否存在
        File input = new File(inputFile);
        if (!input.exists()) {
            System.out.println("Input file does not exist: " + inputFile);
            return;
        }
        
        // 解析输入文件
        FileInputStream in;
        try {
            in = new FileInputStream(inputFile);
        } catch (Exception e) {
            System.err.println("Error processing file: " + e.getMessage());
            return;
        }
        JavaParser javaParser = new JavaParser();
        try {
            CompilationUnit cu = javaParser.parse(in).getResult().orElse(null);
            if (cu == null) {
                System.out.println("failed to parse the file " + inputFile);
                return;
            }
            // 处理import语句
            ArrayList<String> imports = new ArrayList<>();
            cu.findAll(ImportDeclaration.class).forEach(importDecl -> {
                // 获取import语句的完整字符串（如"import com.github.javaparser.JavaParser;"）
                String importContent = importDecl.getNameAsString();
                imports.add(importContent);
            });
        // 处理编译单元中的所有类型声明
        boolean multyWarning = false;
        for (TypeDeclaration<?> decl : cu.findAll(TypeDeclaration.class)) {
            if (!decl.isNestedType()) {
                if (multyWarning) {
                    System.out.println("warning: multiple classes found in " + inputFile);
                    break;
                }
                // 父类和接口
                List<String> implementedInterfaceNames = new ArrayList<>();
                List<String> parentNames = new ArrayList<>();
                if (decl instanceof ClassOrInterfaceDeclaration COIDecl) {
                    COIDecl.getImplementedTypes().forEach((type) -> {
                        implementedInterfaceNames.add(type.getNameAsString());
                    });
                    if (!COIDecl.isInterface()){
                        COIDecl.getExtendedTypes().forEach((type) -> {
                            parentNames.add(type.getNameAsString());
                        });
                    }
                }

                // 方法体
                ArrayList<String> methodBodies = new ArrayList<>();
                // 成员变量
                ArrayList<String> classFields = new ArrayList<>();
                String type = removeMethodBody(decl, methodBodies, classFields);
                decl.getAllContainedComments().forEach(Comment::remove);
                // 输出结果
                try (FileWriter writer = new FileWriter(outputFile)) {
                    // 输出import语句
                    writer.write("'''import\n");
                    for (String importContent : imports) {
                        writer.write(importContent + "\n");
                    }
                    writer.write("''' \n");

                    // 输出类声明
                    writer.write("'''" + type + "\n");
                    writer.write("//classname:" + decl.getNameAsString() + "\n");
                    DefaultPrettyPrinter printer = new DefaultPrettyPrinter();
                    writer.write(printer.print(decl) + "\n''' \n");

                    // 输出父类和接口
                    String parentNamesStr = "None";
                    String implementedInterfaceNamesStr = "None";
                    writer.write("'''parents\n");
                    if (!parentNames.isEmpty())
                        parentNamesStr = String.join(",", parentNames);
                    if (!implementedInterfaceNames.isEmpty())
                        implementedInterfaceNamesStr = String.join(",", implementedInterfaceNames);
                    writer.write(parentNamesStr + "|" + implementedInterfaceNamesStr + "\n");
                    writer.write("''' \n");

                    // 输出成员变量
                    writer.write("'''fields\n");
                    for (String field : classFields) {
                        writer.write(field + "\n");
                    }
                    writer.write("''' \n");

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

    public static String removeMethodBody(TypeDeclaration<?> typeDecl, ArrayList<String> methods, ArrayList<String> fields) {
        return removeMethodBody(typeDecl, methods, fields, new ArrayList<>());
    }

    private static String removeMethodBody(TypeDeclaration<?> typeDecl,
                                           ArrayList<String> methods,
                                           ArrayList<String> fields,
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

        // 组装 外类$内类$... 形式的类名
        ArrayList<String> chain = new ArrayList<>(outers);
        chain.add(typeDecl.getNameAsString());
        String classNameDollar = String.join("$", chain);

        typeDecl.getMembers().forEach(member -> {
            // 处理成员变量
            if (member instanceof FieldDeclaration fieldDecl) {
                String fieldName = fieldDecl.getVariables().get(0).getNameAsString();
                String fieldType = fieldDecl.getElementType().asString();
                String modifiers = String.join(" ", fieldDecl.getModifiers().stream()
                        .map(m -> m.getKeyword().asString())
                        .toList());
//                String fieldInfo = String.format(
//                        "//fieldname:%s::%s type:%s modifiers:%s",
//                        classNameDollar, fieldName, fieldType, modifiers);
                fields.add(fieldDecl.toString());
            }
            // 处理方法
            else if (member instanceof MethodDeclaration method) {
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
            }
            // 处理构造函数
            else if (member instanceof ConstructorDeclaration ctor) {
                if (logMethods) {
                    String parameters = ctor.getParameters().stream()
                            .map(p -> p.getType().asString())
                            .reduce((a, b) -> a + "," + b).orElse("");
                    // 构造：函数名强制为 外类$内类
                    String sig = String.format(
                            "'''method\n//methodname:%s::%s(%s)\n%s\n''' \n",
                            classNameDollar, classNameDollar, parameters, ctor);
                    methods.add(sig);
                }
                ctor.setBody(StaticJavaParser.parseBlock("{}"));
            }
            // 处理内部类
            else if (member instanceof TypeDeclaration) {
                // 递归内部类，链路继续传下去
                removeMethodBody((TypeDeclaration<?>) member, methods, fields, chain);
            }
        });

        return res;
    }

}
