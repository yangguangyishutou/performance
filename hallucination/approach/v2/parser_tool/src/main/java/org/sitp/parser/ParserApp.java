package org.sitp.parser;

import org.sitp.parser.parser.JavaSourceParser;
import org.sitp.parser.util.FileIOUtils;

import java.io.File;

/**
 * Main application entry point for the Java source parser tool.
 * Parses Java source files and extracts structured information into JSON format.
 */
public class ParserApp {

    private static final String USAGE = "Usage: parser.jar <project_path> <output_root_path>\n" +
            "Example: java -jar parser.jar path/to/project path/to/output";

    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println(USAGE);
            return;
        }

        String projectPath = args[0];
        String outputPath = args[1];

        // Validate project directory
        if (!FileIOUtils.isValidDirectory(projectPath)) {
            System.err.println("Error: Project path does not exist or is not a directory: " + projectPath);
            return;
        }

        // Ensure output directory exists
        File outputDir = new File(outputPath);
        if (!outputDir.exists()) {
            outputDir.mkdirs();
        }

        // Process project
        processProject(projectPath, outputPath);
    }

    /**
     * Processes all Java files in a project directory.
     *
     * @param projectPath the project directory path
     * @param outputPath the output directory path
     */
    private static void processProject(String projectPath, String outputPath) {
        File projectDir = new File(projectPath);
        JavaSourceParser parser = new JavaSourceParser();

        File[] sourceFiles = projectDir.listFiles();
        if (sourceFiles == null) {
            System.err.println("Failed to list files in project: " + projectPath);
            return;
        }

        int successCount = 0;
        int failureCount = 0;

        for (File file : sourceFiles) {
            if (!file.isFile()) {
                continue;
            }

            String fileName = file.getName();
            if (!FileIOUtils.hasExtension(fileName, "java")) {
                continue;
            }

            String baseFileName = FileIOUtils.getFileNameWithoutExtension(fileName);
            String inputFilePath = FileIOUtils.joinPath(projectPath, fileName);
            String outputFilePath = FileIOUtils.joinPath(outputPath, baseFileName + ".json");

            boolean success = parser.parseJavaFile(inputFilePath, outputFilePath);
            if (success) {
                successCount++;
            } else {
                failureCount++;
            }
        }

        System.out.println("\n=== Parsing Summary ===");
        System.out.println("Successfully processed: " + successCount);
        System.out.println("Failed: " + failureCount);
    }
}
