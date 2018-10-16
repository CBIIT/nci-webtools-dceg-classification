/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gov.nih.nci.jobs;

import gov.nih.nci.queue.model.QueueModel;
import gov.nih.nci.queue.utils.*;
import java.io.*;
import java.util.Date;
import java.util.logging.*;
import org.codehaus.jackson.JsonNode;
import org.codehaus.jackson.map.ObjectMapper;
import org.quartz.*;

/**
 *
 * @author Yutao
 */
public class SoccerJob implements Job {
    private static final Logger LOGGER = Logger.getLogger(SoccerJob.class.getName());
    private static final QueueConsumerUtil qcu = new QueueConsumerUtil();
    private static final String outputFilePre = "SoccerResults-"; // Soccer App will add this prefix.
    private static final String NUMBER_OF_LINES_TRACK_FILE_NAME = "soccerStats.csv";

    @Override
    @SuppressWarnings("empty-statement")
    public void execute(JobExecutionContext context) throws JobExecutionException {
        // Get data passed in.
        JobDataMap data = context.getJobDetail().getJobDataMap();
        String cmd = (String) data.getString("cmd");

        /* Processing the message */
        QueueModel qm = qcu.cousume();

        if (qm != null) {
            String path = qm.getPath();
            String fileName = qm.getFileName();    // The input file name generated by upload servlet, not the original file name.
            String email = qm.getEmail();
            String timeStamp = qm.getTimeStamp();
            String outputDir = qm.getOutputDir();
            LOGGER.log(Level.INFO, "{0}", qm);

            // get original file name
            // New requirement in Mar, 2015,
            // Put this informaiton in email body.
            // The original name is in the <fileName>.json file generated by servlets.
            String originalFileName = getOriginalFileName(fileName, path);

            // Track the numbers of lines processed.
            // New requiremnt in Apr, 2015
            // This information will be stored in soccerStats.csv
            // Format: Timestamp, Input  file name, Number of lines
            // Track asynchronous data process only
            logNumberOfLines(NUMBER_OF_LINES_TRACK_FILE_NAME, originalFileName, fileName, path);

            // Construct a unique ID to track the output file.
            String outputFileId = new UniqueIdUtil(fileName).getOutputUniqueID();

            // Save metadata info.
            try {
                new MetadataFileUtil(outputFileId, outputDir).generateMetadataFile(new ObjectMapper().writeValueAsString(qm));
            } catch(IOException e){;}

            // Run command.
            String outputFile = outputDir + File.separator + outputFilePre + fileName; // the extected soccer result file name.
            String outputFile2 = outputDir + File.separator + outputFileId; // the uniqueId
            String outputFile3 = outputDir + File.separator + outputFileId + ".png"; // the image file.
            String fullCmd = new StringBuilder(cmd).append(" ")
                    .append(path).append(File.separator).append(fileName).append(" ")
                    .append(outputFile).append(" ")
                    .append(outputFile3).append(" ")
                    .toString();
            LOGGER.info("Full Command: " + fullCmd);
            if (ExeCommand(fullCmd)) {
                // rename to the outputFileId.
                renameFileName(outputFile, outputFile2);

                // Send email.
                String from = "SOCcer <do.not.reply@mail.nih.gov>";
                boolean isMailSent = new MailUtil().mailTo(from, email, composeMailTitle(), composeMailBody(timeStamp, outputFileId, originalFileName));
                if (isMailSent) {
                    LOGGER.log(Level.INFO, "Message has been sent to {0} successfully.", email);
                } else {
                    LOGGER.log(Level.SEVERE,"Failed to send email. Please check email settings or security settings.");
                }
            }
        } else {
            LOGGER.info("."); // indicating the applicaiton is running.
        }
    }

    /*
     * Execute shell command.
     */
    private boolean ExeCommand(String cmd) {
        boolean bRet = false;
        try {
            Process p = Runtime.getRuntime().exec(cmd);

            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }

            // check result.
            if (p.waitFor() == 0) {
                bRet = true;
            }
        } catch (IOException | InterruptedException ie) {
            LOGGER.log(Level.SEVERE, "Caught IOException and InterruptedException. '{'0'}'\r\n{0}", ie.getMessage());
        }

        return bRet;
    }

    /*
     * renamte filename.
     */
    public boolean renameFileName(String oldName, String newName) {
        System.out.println(new StringBuilder("Rename ")
                .append(oldName)
                .append(" to ")
                .append(newName).toString());

        File fileOld = new File(oldName);
        File fileNew = new File(newName);
        if (fileOld.exists()) {
            fileOld.renameTo(fileNew);
            return true;
        } else {
            return false;
        }
    }

    /*
     * Get original file name
     * fileName: {fileName: blabla.csv ...}
     * path: {...; path: blabal; ...}
     */
    private String getOriginalFileName(String fileName, String path) {
        String retString = "";

        // get jsonFilePath
        String jsonFilePath = path + File.separator + fileName + ".json";
        // read file to string
        String jsonString = "";
        try (BufferedReader br = new BufferedReader(new FileReader(jsonFilePath)))
        {
            String sCurrentLine;
            while ((sCurrentLine = br.readLine()) != null) {
                jsonString += sCurrentLine;
            }
        } catch (IOException e) {
            LOGGER.log(Level.SEVERE, "{0} does not exist! Cannot get original file name! {1}", new Object[]{jsonFilePath, e.getMessage()});
            return retString;
        }

        // parse json string.
        LOGGER.log(Level.INFO, "{0} : {1}", new Object[]{jsonFilePath, jsonString});
        ObjectMapper mapper = new ObjectMapper();
        try {
            JsonNode actualObj = mapper.readTree(jsonString);
            retString = actualObj.get("fileName").toString().replace("\"", "");
            LOGGER.log(Level.INFO, "Original File Name: {0}", retString);
        } catch(IOException e) {
        }

        return retString;
    }

    // Log numbers of lines of the input file.
    private void logNumberOfLines(String logNumberOfLinesFileName, String originalFileName, String fileName, String path) {
        String deployTargetFolder = PropertiesUtil.getProperty("deploy.target.dir").trim();
        String logNumberOfLinesFilePath = deployTargetFolder + File.separator + logNumberOfLinesFileName;

        try {
            File file = new File(logNumberOfLinesFilePath);
            // if file doesnt exists, then create it
            if (!file.exists()) {
                file.createNewFile();
                LOGGER.log(Level.INFO, "Created the log file. <{0}>", logNumberOfLinesFilePath);

                FileWriter fw = new FileWriter(logNumberOfLinesFilePath);
                BufferedWriter bw = new BufferedWriter(fw);
                bw.write("Timestamp, Input  file name, Number of lines");
                bw.close();
            }

            // Check whether the file is occupied by other processes.
            if(file.canWrite()) {
                // construct string. Format: Timestamp, Input  file name, Number of lines
                String logLineContent = "\r\n" + new Date() + "," + originalFileName + "," + getNumberLines(new File(path + File.separator + fileName));
                FileWriter fw = new FileWriter(file.getAbsoluteFile(), true); // append.
                BufferedWriter bw = new BufferedWriter(fw);
                bw.write(logLineContent);
                bw.close();
                LOGGER.log(Level.INFO, "Logged number of lines to {0} successfully.", logNumberOfLinesFilePath);
            }
            else {
                LOGGER.log(Level.WARNING, "Multipe Computing Applications are running. They may conflict when logging number of lines to the file: {0}", logNumberOfLinesFilePath);
            }
        } catch (IOException e) {
            LOGGER.log(Level.SEVERE, "Failed to log number of lines. {0}", e.getMessage());
        }
    }

    // Get numbers of lines of a file
    @SuppressWarnings("empty-statement")
    private int getNumberLines(File file) throws IOException {
        int numLines;
        try (BufferedReader in = new BufferedReader(new FileReader(file))) {
            in.readLine(); // Ignore the first line.
            for(numLines = 0; in.readLine() != null; numLines++);
        }
        return numLines;
    }

    // Compose Mail Title.
    private String composeMailTitle() {
        return "Your request has been processed";
    }

    // Compose Mail Body.
    private String composeMailBody(String timeStamp, String outputFileId, String originalFileName) {
        // get hostname automatically.
        String hostname = PropertiesUtil.getProperty("soccer.remote.web.host").trim();
        String port = PropertiesUtil.getProperty("soccer.remote.web.port").trim();

        if(hostname == null) {
            return "";
        }
        if(port == null || port.length() == 0) {
            port = "80";
        }

        // remove extra \ from the original file name.
        originalFileName = originalFileName.replace("\\\\", "\\");

        // construct the http link.
        StringBuilder accessLinkSB = new StringBuilder("http://");
        accessLinkSB.append(hostname)
                .append(":")
                .append(port)
                .append("/soccer/index.html?fileid=")
                .append(outputFileId);
        return new StringBuilder("\r\nThe file (")
                .append(originalFileName)
                .append(") you uploaded on ")
                .append(timeStamp)
                .append(" has been processed. ")
                .append("\r\nYou can view the result page at: ")
                .append(accessLinkSB.toString())
                .append(".  This link will expire two weeks from today.")
                .append("\r\n\r\n - SOCcer Team\r\n(Note:  Please do not reply to this email. If you need assistance, please contact NCISOCcerWebAdmin@mail.nih.gov)")
                .toString();
    }
}