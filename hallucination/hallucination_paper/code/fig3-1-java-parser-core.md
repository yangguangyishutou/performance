
```java
public static void forOneFileNew(String inputFile, String outputFile) {
    // Parse input file using JavaParser
    FileInputStream in = new FileInputStream(inputFile);
    JavaParser javaParser = new JavaParser();
    CompilationUnit cu = javaParser.parse(in).getResult().orElse(null);

    // Extract imports, classes, and methods
    ArrayList<String> imports = new ArrayList<>();
    cu.findAll(ImportDeclaration.class).forEach(importDecl -> {
        imports.add(importDecl.getNameAsString());
    });

    // Process each type declaration
    for (TypeDeclaration<?> decl : cu.findAll(TypeDeclaration.class)) {
        if (!decl.isNestedType()) {
            processTypeDeclaration(decl, imports, outputFile);
        }
    }
}
```