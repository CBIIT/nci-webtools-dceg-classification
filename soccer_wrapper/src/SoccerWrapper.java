/**
 * SoccerWrapper allows us to call soccer methods via cli.
 *
 * SOCcer model versions 1.0 and 2.0 (formerly 1.1) are supported.
 */

import org.apache.commons.cli.*;

import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Paths;
import java.util.logging.LogManager;

public class SoccerWrapper {

    /**
     * Set up the CLI for SoccerWrapper
     * @param args
     * @throws Exception
     */
    public static void main(String[] args) throws Exception {

        int modelVersion = 2;
        File inputFile = null, outputFile = null, modelFile = null, jarFile = null;
        String method = null;

        // parse arguments
        try {
            CommandLine cmd = new DefaultParser().parse(getOptions(), args);

            if (cmd.hasOption("jar-file"))
                jarFile = new File(cmd.getOptionValue("jar-file"));
            else
                throw new ParseException("Please provide a SOCcer jar file");

            if (cmd.hasOption("method"))
                method = cmd.getOptionValue("method");
            else
                throw new ParseException("Please provide a method to run (estimate-runtime, validate-file, or code-file)");

            if (cmd.hasOption("model-version"))
                modelVersion = Integer.parseInt(cmd.getOptionValue("model-version"));
            if (modelVersion != 1 && modelVersion != 2)
                throw new ParseException("Please provide a valid model version (1.0 or 2.0)");

            if (cmd.hasOption("model-file"))
                modelFile = new File(cmd.getOptionValue("model-file"));
            else if (modelVersion == 2 && method.equals("code-file"))
                throw new ParseException("SOCcer v2.0 requires a model file");

            if (cmd.hasOption("input-file"))
                inputFile = new File(cmd.getOptionValue("input-file"));
            else
                throw new ParseException("Please provide an input file");

            if (cmd.hasOption("output-file"))
                outputFile = new File(cmd.getOptionValue("output-file"));
            else if (method.equals("code-file"))
                throw new ParseException("Please provide an output file");

        } catch (Exception e) {
            System.err.println(e.getMessage());
            printUsage("java -jar soccer-wrapper.jar", getOptions());
            System.exit(-1);
        }

        // by default, use the "wordnet" folder in our current directory
        if (System.getProperty("gov.nih.cit.soccer.wordnet.dir") == null)
            System.setProperty("gov.nih.cit.soccer.wordnet.dir", "wordnet");

        // set the output directory to the one specified in the output file
        System.setProperty("gov.nih.cit.soccer.output.dir",
            outputFile != null
                ? outputFile.getAbsoluteFile().getParentFile().getAbsolutePath()
                : System.getProperty("user.dir")
        );

        // determine the SOCcer class name from the model version
        String soccerClassName = modelVersion == 1
                ? "gov.nih.cit.soccer.Soccer"
                : "gov.nih.cit.soccer.SOCcer";

        // create an instance of SOCcer while suppressing output
        LogManager.getLogManager().reset();
        Object soccerInstance = getInstance(jarFile, soccerClassName);

        try {
            switch (method) {
                case "code-file":
                    codeFile(soccerInstance, modelVersion, modelFile, inputFile, outputFile);
                    break;

                case "estimate-runtime":
                    System.out.println(getEstimatedTime(soccerInstance, inputFile));
                    break;

                case "validate-file":
                    validateFile(soccerInstance, inputFile);
                    break;
            }
        } catch (Exception e) {
            if (e.getCause() != null)
                System.err.println(e.getCause().getMessage());
            else
                e.printStackTrace();
            System.exit(1);
        }
    }

    /**
     * Prints the usage for a set of Options
     * @param options The options we wish to display the usage for
     */
    public static void printUsage(String header, Options options) {
        HelpFormatter helpFormatter = new HelpFormatter();
        helpFormatter.setOptionComparator(null);
        helpFormatter.printHelp(header + "\n\n", options);
    }

    /**
     * @return Options for the cli parser
     */
    public static Options getOptions() {
        return new Options()
            .addOption("v", "model-version", true, "SOCcer model version (default: 2.0)")
            .addOption("m", "method", true, "SOCcer method to call (estimate-runtime, validate-file, code-file)")
            .addOption("i", "input-file", true, "Path to the input file (required)")
            .addOption("o", "output-file", true, "Path to the output file (required for code-file method)")
            .addOption("j", "jar-file", true, "Path to the SOCcer jar file (required)")
            .addOption("f", "model-file", true, "Path to the SOCcer model (required for model 2.0)");
    }

    /**
     * Calls SOCcer's getEsimatedTime method
     *
     * @param soccerInstance The SOCcer object that has been loaded from the jar file
     * @param inputFile The file that should have its runtime estimated
     * @return Output from the SOCcer jar's getEstimatedTime method
     * @throws Exception
     */
    public static double getEstimatedTime(Object soccerInstance, File inputFile) throws Exception {
        return (Double) soccerInstance
            .getClass()
            .getMethod("getEstimatedTime", File.class)
            .invoke(soccerInstance, inputFile);
    }

    /**
     * Calls SOCcer's validateFile method
     *
     * @param soccerInstance The SOCcer object that has been loaded from the jar file
     * @param inputFile The file that should be validated
     * @throws Exception This method throws an Exception if validation fails
     */
    public static void validateFile(Object soccerInstance, File inputFile) throws Exception {
        soccerInstance
            .getClass()
            .getMethod("validateFile", File.class)
            .invoke(soccerInstance, inputFile);
    }

    /**
     * Calls SOCcer's codeFile method, which has a different signature depending on the model version
     *
     * For model 1.0, the output file name is created as SoccerResults-" + inputFile.getName()
     * The output directory is specified by the system property: "gov.nih.cit.soccer.output.dir"
     * This method renames SOCcer 1.0's results file to the outputFile specified in the parameters.
     *
     * Model 1.0 also requires that the "gov.nih.cit.soccer.wordnet.dir" property be set to a directory
     * containing WordNet 3.1.
     *
     * Model 1.0 does not require a model file.
     *
     * For model 2.0, we should provide the model file.
     * Model 2.0 does not require the gov.nih.cit.soccer.wordnet.dir or the gov.nih.cit.soccer.output.dir
     * properties to be specified.
     *
     * @param soccerInstance
     * @param modelVersion
     * @param modelFile
     * @param inputFile
     * @param outputFile
     * @throws Exception
     */
    public static void codeFile(Object soccerInstance, int modelVersion, File modelFile, File inputFile, File outputFile) throws Exception {
        if (modelVersion == 1) {
            soccerInstance
                .getClass()
                .getMethod("codeFile", File.class)
                .invoke(soccerInstance, inputFile);

            // rename output file
            Paths.get(
                System.getProperty("gov.nih.cit.soccer.output.dir"),
                "SoccerResults-" + inputFile.getName()
            ).toFile().renameTo(outputFile);

        } else if (modelVersion == 2) {
            soccerInstance
                .getClass()
                .getMethod("codeFile", File.class, File.class, File.class, int.class)
                .invoke(soccerInstance, modelFile, inputFile, outputFile, 1);
        }
    }

    /**
     * Gets an instance of an object from a jar file given its full class name
     * @param jarFile The jar file to load
     * @param className The name of the class to instantiate
     * @return Object an instance of the specified class
     * @throws Exception
     */
    public static Object getInstance(File jarFile, String className) throws Exception {
        URLClassLoader classLoader = URLClassLoader.newInstance(new URL[] { jarFile.toURI().toURL() });
        return classLoader.loadClass(className).newInstance();
    }
}
