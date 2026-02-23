package org.sitp.parser.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.sitp.parser.model.JavaFileInfo;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Utility class for file I/O operations.
 */
public class FileIOUtils {

    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().setPrettyPrinting().create();

    /**
     * Ensures the parent directory of a file path exists.
     *
     * @param filePath the file path
     * @return the parent directory File object
     */
    public static File ensureParentDirectoryExists(String filePath) {
        Path path = Paths.get(filePath);
        Path parentPath = path.getParent();
        if (parentPath != null) {
            File parentDir = parentPath.toFile();
            if (!parentDir.exists()) {
                parentDir.mkdirs();
            }
            return parentDir;
        }
        return null;
    }

    /**
     * Checks if a file exists.
     *
     * @param filePath the file path to check
     * @return true if the file exists, false otherwise
     */
    public static boolean fileExists(String filePath) {
        return Paths.get(filePath).toFile().exists();
    }

    /**
     * Checks if a directory exists and is valid.
     *
     * @param dirPath the directory path to check
     * @return true if the directory exists and is valid, false otherwise
     */
    public static boolean isValidDirectory(String dirPath) {
        File dir = new File(dirPath);
        return dir.exists() && dir.isDirectory();
    }

    /**
     * Writes JavaFileInfo to a JSON file.
     *
     * @param fileInfo the JavaFileInfo to write
     * @param outputPath the output file path
     * @throws IOException if an I/O error occurs
     */
    public static void writeToJson(JavaFileInfo fileInfo, String outputPath) throws IOException {
        ensureParentDirectoryExists(outputPath);
        try (FileWriter writer = new FileWriter(outputPath)) {
            GSON.toJson(fileInfo, writer);
        }
    }

    /**
     * Combines path parts using the system's file separator.
     *
     * @param parts the path parts
     * @return the combined path
     */
    public static String joinPath(String... parts) {
        return String.join(File.separator, parts);
    }

    /**
     * Gets the file name without extension.
     *
     * @param fileName the file name
     * @return the file name without extension
     */
    public static String getFileNameWithoutExtension(String fileName) {
        int lastDotIndex = fileName.lastIndexOf('.');
        if (lastDotIndex > 0) {
            return fileName.substring(0, lastDotIndex);
        }
        return fileName;
    }

    /**
     * Checks if a file has the specified extension.
     *
     * @param fileName the file name
     * @param extension the extension to check (without dot)
     * @return true if the file has the specified extension
     */
    public static boolean hasExtension(String fileName, String extension) {
        int lastDotIndex = fileName.lastIndexOf('.');
        if (lastDotIndex > 0 && lastDotIndex < fileName.length() - 1) {
            String fileExtension = fileName.substring(lastDotIndex + 1);
            return fileExtension.equalsIgnoreCase(extension);
        }
        return false;
    }
}
