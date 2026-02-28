package org.sitp.parser.parser;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.comments.Comment;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.stmt.Statement;
import com.github.javaparser.printer.DefaultPrettyPrinter;
import org.sitp.parser.model.JavaFileInfo;
import org.sitp.parser.model.MethodInfo;
import org.sitp.parser.util.FileIOUtils;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * Service class for parsing Java source files and extracting structured information.
 */
public class JavaSourceParser {

    private final JavaParser parser;

    public JavaSourceParser() {
        this.parser = new JavaParser();
    }

    /**
     * Parses a Java source file and saves the extracted information as JSON.
     *
     * @param inputFilePath the input Java file path
     * @param outputFilePath the output JSON file path
     * @return true if parsing succeeded, false otherwise
     */
    public boolean parseJavaFile(String inputFilePath, String outputFilePath) {
        // Validate input file
        if (!FileIOUtils.fileExists(inputFilePath)) {
            System.err.println("Input file does not exist: " + inputFilePath);
            return false;
        }

        // Parse the file
        CompilationUnit compilationUnit = parseCompilationUnit(inputFilePath);
        if (compilationUnit == null) {
            return false;
        }

        // Process all type declarations in the file
        List<TypeDeclaration<?>> typeDeclarations = new ArrayList<>();
        compilationUnit.findAll(ClassOrInterfaceDeclaration.class).forEach(typeDeclarations::add);
        compilationUnit.findAll(EnumDeclaration.class).forEach(typeDeclarations::add);
        compilationUnit.findAll(RecordDeclaration.class).forEach(typeDeclarations::add);

        boolean hasProcessed = false;

        for (TypeDeclaration<?> declaration : typeDeclarations) {
            if (declaration.isNestedType()) {
                System.out.println("Warning: Nested type found in " + inputFilePath + ", skipping");
                continue;
            }

            if (hasProcessed) {
                System.out.println("Warning: Multiple top-level classes found in " + inputFilePath);
                break;
            }

            JavaFileInfo fileInfo = extractTypeInfo(compilationUnit, declaration);
            fileInfo.setFilePath(inputFilePath);
            try {
                FileIOUtils.writeToJson(fileInfo, outputFilePath);
                System.out.println("Processed file saved to: " + outputFilePath);
                hasProcessed = true;
            } catch (IOException e) {
                System.err.println("Error writing output file: " + e.getMessage());
            }
        }

        return hasProcessed;
    }

    /**
     * Parses a Java file into a CompilationUnit.
     *
     * @param filePath the file path to parse
     * @return the CompilationUnit, or null if parsing failed
     */
    private CompilationUnit parseCompilationUnit(String filePath) {
        try (FileInputStream inputStream = new FileInputStream(filePath)) {
            return parser.parse(inputStream).getResult().orElse(null);
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
            return null;
        }
    }

    /**
     * Extracts type information from a type declaration.
     *
     * @param compilationUnit the compilation unit
     * @param declaration the type declaration
     * @return the extracted JavaFileInfo
     */
    private JavaFileInfo extractTypeInfo(CompilationUnit compilationUnit, TypeDeclaration<?> declaration) {
        JavaFileInfo fileInfo = new JavaFileInfo();

        // Extract imports
        List<String> imports = extractImports(compilationUnit);
        fileInfo.setImports(imports);

        // Extract parent classes and interfaces
        List<String> parentClasses = new ArrayList<>();
        List<String> interfaces = new ArrayList<>();
        extractInheritanceInfo(declaration, parentClasses, interfaces);

        fileInfo.setParentClass(parentClasses.isEmpty() ? "" : String.join(",", parentClasses));
        fileInfo.setInterfaces(interfaces);

        // Extract methods and fields
        List<MethodInfo> methods = new ArrayList<>();
        List<String> fields = new ArrayList<>();
        int[] methodCount = new int[1]; // Use array to hold mutable count
        String type = extractMembersAndRemoveBodies(declaration, methods, fields, methodCount, new ArrayList<>());

        // Remove comments from declaration
        declaration.getAllContainedComments().forEach(Comment::remove);

        // Generate class declaration string
        fileInfo.setClassDeclaration(new DefaultPrettyPrinter().print(declaration));
        fileInfo.setType(type);
        fileInfo.setClassName(declaration.getNameAsString());
        fileInfo.setMethods(methods);
        fileInfo.setMethodCount(methodCount[0]);
        fileInfo.setFieldDeclarations(fields);

        return fileInfo;
    }

    /**
     * Extracts import statements from a compilation unit.
     *
     * @param compilationUnit the compilation unit
     * @return list of import statements
     */
    private List<String> extractImports(CompilationUnit compilationUnit) {
        List<String> imports = new ArrayList<>();
        compilationUnit.findAll(ImportDeclaration.class).forEach(importDecl ->
                imports.add(importDecl.getNameAsString())
        );
        return imports;
    }

    /**
     * Extracts inheritance information (parent classes and interfaces).
     *
     * @param declaration the type declaration
     * @param parentClasses list to populate with parent class names
     * @param interfaces list to populate with interface names
     */
    private void extractInheritanceInfo(TypeDeclaration<?> declaration,
                                        List<String> parentClasses,
                                        List<String> interfaces) {
        if (declaration instanceof ClassOrInterfaceDeclaration coiDeclaration) {
            coiDeclaration.getImplementedTypes().forEach(type ->
                    interfaces.add(type.getNameAsString())
            );

            if (!coiDeclaration.isInterface()) {
                coiDeclaration.getExtendedTypes().forEach(type ->
                        parentClasses.add(type.getNameAsString())
                );
            }
        }
    }

    /**
     * Extracts member information (methods and fields) and removes method bodies.
     *
     * @param typeDeclaration the type declaration
     * @param methods list to populate with method information
     * @param fields list to populate with field declarations
     * @return the type name ("class", "interface", "enum", or "unknown")
     */
    private String extractMembersAndRemoveBodies(TypeDeclaration<?> typeDeclaration,
                                                  List<MethodInfo> methods,
                                                  List<String> fields) {
        return extractMembersAndRemoveBodies(typeDeclaration, methods, fields, new int[1], new ArrayList<>());
    }

    /**
     * Recursively extracts member information and removes method bodies.
     *
     * @param typeDeclaration the type declaration
     * @param methods list to populate with method information
     * @param fields list to populate with field declarations
     * @param methodCount array to hold total method count (including interface methods)
     * @param outerClassNames chain of outer class names for nested types
     * @return the type name
     */
    private String extractMembersAndRemoveBodies(TypeDeclaration<?> typeDeclaration,
                                                  List<MethodInfo> methods,
                                                  List<String> fields,
                                                  int[] methodCount,
                                                  List<String> outerClassNames) {
        String type;
        boolean shouldLogMethods;

        // Determine type and whether to log methods
        if (typeDeclaration instanceof ClassOrInterfaceDeclaration coiDeclaration) {
            shouldLogMethods = !coiDeclaration.isInterface();
            type = coiDeclaration.isInterface() ? "interface" : "class";
        } else if (typeDeclaration instanceof EnumDeclaration) {
            shouldLogMethods = true;
            type = "enum";
            System.out.println("Warning: Enum found in " + typeDeclaration.getNameAsString());
        } else {
            System.out.println("Warning: Unknown type in " + typeDeclaration.getNameAsString());
            return "unknown";
        }

        // Build fully qualified name with outer classes (e.g., Outer$Inner)
        List<String> classNameChain = new ArrayList<>(outerClassNames);
        classNameChain.add(typeDeclaration.getNameAsString());
        String qualifiedName = String.join("$", classNameChain);

        // Process all members
        typeDeclaration.getMembers().forEach(member -> {
            // System.out.println("Processing member: " + member);
            
            if (member instanceof FieldDeclaration fieldDeclaration) {
                handleFieldDeclaration(fieldDeclaration, fields);
            } else if (member instanceof MethodDeclaration methodDeclaration) {
                handleMethodDeclaration(methodDeclaration, methods, qualifiedName, shouldLogMethods, methodCount);
            } else if (member instanceof ConstructorDeclaration constructorDeclaration) {
                handleConstructorDeclaration(constructorDeclaration, methods, qualifiedName, shouldLogMethods, methodCount);
            } else if (member instanceof TypeDeclaration<?> nestedType) {
                // Recursively handle nested types
                extractMembersAndRemoveBodies(nestedType, methods, fields, methodCount, classNameChain);
            }
        });

        return type;
    }

    /**
     * Handles a field declaration.
     *
     * @param fieldDeclaration the field declaration
     * @param fields list to populate with field declarations
     */
    private void handleFieldDeclaration(FieldDeclaration fieldDeclaration, List<String> fields) {
        fields.add(fieldDeclaration.toString());
    }

    /**
     * Handles a method declaration.
     *
     * @param methodDeclaration the method declaration
     * @param methods list to populate with method information
     * @param qualifiedName the qualified class name
     * @param shouldLog whether to log this method
     * @param methodCount array to hold total method count
     */
    private void handleMethodDeclaration(MethodDeclaration methodDeclaration,
                                         List<MethodInfo> methods,
                                         String qualifiedName,
                                         boolean shouldLog,
                                         int[] methodCount) {
        methodCount[0]++;
        methodDeclaration.getBody().ifPresent(body -> {
            // Count this method regardless of whether we log it
            String methodName = methodDeclaration.getNameAsString();
            String parameters = extractParameterTypes(methodDeclaration);
            String signature = String.format("%s:%s(%s)", qualifiedName, methodName, parameters);
            // System.out.println("Found method: " + signature);

            if (shouldLog) {
                
                String comment = methodDeclaration.getComment()
                        .map(Comment::getContent)
                        .orElse("");

                // Clone the method declaration to avoid modifying the original when removing comments
                MethodDeclaration clonedMethod = methodDeclaration.clone();
                // Remove all comments from the method body
                clonedMethod.getAllContainedComments().forEach(Comment::remove);
                String methodBody = clonedMethod.toString();

                // Count statements in the method body
                int statementCount = countStatements(body);

                methods.add(new MethodInfo(methodName, signature, comment, methodBody, statementCount));
            }
            methodDeclaration.setBody(null);
        });
    }

    /**
     * Handles a constructor declaration.
     *
     * @param constructorDeclaration the constructor declaration
     * @param methods list to populate with method information
     * @param qualifiedName the qualified class name
     * @param shouldLog whether to log this constructor
     * @param methodCount array to hold total method count
     */
    private void handleConstructorDeclaration(ConstructorDeclaration constructorDeclaration,
                                               List<MethodInfo> methods,
                                               String qualifiedName,
                                               boolean shouldLog,
                                               int[] methodCount) {
        BlockStmt body = constructorDeclaration.getBody();
        if (body != null) {
            // Count this constructor regardless of whether we log it
            methodCount[0]++;

            if (shouldLog) {
                String parameters = extractParameterTypes(constructorDeclaration);
                String signature = String.format("%s:%s(%s)", qualifiedName, qualifiedName, parameters);
                String comment = constructorDeclaration.getComment()
                        .map(Comment::getContent)
                        .orElse("");

                // Clone the constructor declaration to avoid modifying the original when removing comments
                ConstructorDeclaration clonedConstructor = constructorDeclaration.clone();
                // Remove all comments from the constructor body
                clonedConstructor.getAllContainedComments().forEach(Comment::remove);
                String constructorBody = clonedConstructor.toString();

                // Count statements in the constructor body
                int statementCount = countStatements(body);

                methods.add(new MethodInfo(qualifiedName, signature, comment, constructorBody, statementCount));
            }
        }
        constructorDeclaration.setBody(com.github.javaparser.StaticJavaParser.parseBlock("{}"));
    }

    /**
     * Extracts parameter types from a callable declaration (method or constructor).
     *
     * @param callable the callable declaration
     * @return comma-separated parameter types
     */
    private String extractParameterTypes(CallableDeclaration<?> callable) {
        return callable.getParameters().stream()
                .map(p -> p.getType().asString())
                .reduce((a, b) -> a + "," + b)
                .orElse("");
    }

    /**
     * Counts the number of statements in a method body, including nested statements.
     * This recursively counts all statements in blocks (if-else, for, while, etc.).
     *
     * @param body the method body block
     * @return the number of statements
     */
    private int countStatements(BlockStmt body) {
        if (body == null || body.getStatements() == null) {
            return 0;
        }

        int count = 0;
        for (Statement stmt : body.getStatements()) {
            count++;  // Count this statement
            // Recursively count statements in nested blocks
            count += countNestedStatements(stmt);
        }

        return count;
    }

    /**
     * Recursively counts statements in nested blocks within a statement.
     *
     * @param stmt the statement to examine
     * @return the number of nested statements
     */
    private int countNestedStatements(Statement stmt) {
        // Find all BlockStmt nodes within this statement and count their statements
        List<BlockStmt> blocks = new ArrayList<>();
        stmt.findAll(BlockStmt.class).forEach(blocks::add);

        int count = 0;
        for (BlockStmt block : blocks) {
            if (block.getStatements() != null) {
                count += block.getStatements().size();
            }
        }
        return count;
    }
}
