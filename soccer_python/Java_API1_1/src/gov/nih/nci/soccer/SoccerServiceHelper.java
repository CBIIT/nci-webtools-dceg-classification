/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gov.nih.nci.soccer;

import gov.nih.cit.soccer.SOCcer;
import java.io.IOException;
import java.io.*;
import java.util.logging.*;

/**
 *
 * @author Yutao
 */
public class SoccerServiceHelper {
    private final static Logger LOGGER = Logger.getLogger(SoccerServiceHelper.class.getCanonicalName());

    private final SOCcer soc = new SOCcer();
    private final String outputDir;
    private final String outputFilePre = "SoccerResults-";

    public SoccerServiceHelper(String outputDir) {
        this.outputDir = outputDir;
    }

    /*
     * Algorithom to process the file
     * OR
     * Invoke shell command(s) to process the input file.
     */
    public void ProcessingFile(String modelFilePath,File _fileIn, File _fileOut, int numThreads) throws IOException   {
        // Process the input file and generate a new output file.
        // By soccer, the output file name would be: SoccerResults-<input_file_name>

        InputStream modelInputStream = null;
        File modelFile = new File(modelFilePath);
        if (modelFile.exists()) {
            modelInputStream = new FileInputStream(modelFile);
        } else {
            modelInputStream = SoccerServiceHelper.class.getClassLoader().getResourceAsStream(modelFilePath);
        }

        soc.codeFile(modelInputStream,_fileIn, _fileOut, numThreads);

        // Rename output file (SoccerResults-soccer_dataset0.csv) to _fileOutput.
        // Removing Prefix "SoccerResults-".
        String generatedFilePath = outputDir + File.separator + outputFilePre + _fileIn.getName();
        LOGGER.log(Level.INFO, "SOCcer ouput File: {0}", generatedFilePath);
        File fileOutput = new File(generatedFilePath);
        if (fileOutput.exists() && _fileOut != null) {
            fileOutput.renameTo(_fileOut);
        } else {
            LOGGER.log(Level.SEVERE, "{0} does not exist!", generatedFilePath);
        }
    }

    // Get number of lines of the input file.
    @SuppressWarnings("empty-statement")
    public int getNumberLines(File _file) throws IOException {
        int numLines;
        try (BufferedReader in = new BufferedReader(new FileReader(_file))) {
            in.readLine();
            for (numLines = 0; in.readLine() != null; numLines++);
        }
        return numLines;
    }

    // Get Estimate Processing Time
    //public double getEstimatedTime(String _absoluteInputFileName) throws IOException {
      //  return Math.round(soc.getEstimatedTime(_absoluteInputFileName) * 100.0) / 100.0;
   // }
}
