package gov.nih.nci.queue.api;

import gov.nih.nci.queue.model.ResponseModel;
import gov.nih.nci.queue.utils.MetadataFileUtil;
import gov.nih.nci.queue.utils.PropertiesUtil;
import gov.nih.nci.soccer.InputFileValidator;
import gov.nih.nci.soccer.SoccerServiceHelper;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Created by yankovsr on 4/4/2017.
 */
public class FileUpload {
    private static final long serialVersionUID = 4863936005391033592L;
    private static final Logger LOGGER = Logger.getLogger(FileUpload.class.getCanonicalName());

    public static void main(String[] args) {
        String path = args[0];
        String originalFileName = args[1];
        String fileType = args[2];

        FileUpload fu = new FileUpload();
        fu.upload(path, originalFileName, fileType);
    }

    private String upload(String absoluteInputFileName, String originalFileName, String fileType) {

        // Create an object for JSON response.
        ResponseModel rm = new ResponseModel();

        // Get property values.
        // SOCcer related.
        final Double estimatedThreshhold = Double.valueOf(PropertiesUtil.getProperty("gov.nih.nci.soccer.computing.time.threshhold").trim());

        // FileUpload Settings.
        final String repositoryPath = PropertiesUtil.getProperty("gov.nih.nci.queue.repository.dir");
        final String strOutputDir = PropertiesUtil.getProperty("gov.nih.cit.soccer.output.dir").trim();
        final long fileSizeMax = 10000000000L; // 10G
        LOGGER.log(Level.INFO, "repository.dir: {0}, filesize.max: {1}, time.threshhold: {2}",
                new Object[]{repositoryPath, fileSizeMax, estimatedThreshhold});

        try {
            File inputFile = new File(absoluteInputFileName);
            String fileName = originalFileName;
            rm.setFileName(fileName);
            long sizeInBytes = inputFile.length();
            rm.setFileSize(String.valueOf(sizeInBytes));
            String inputFileId = inputFile.getName();
            rm.setInputFileId(inputFileId);
            rm.setFileType(fileType);


            rm.setRepositoryPath(repositoryPath);

            // Validation.
            InputFileValidator validator = new InputFileValidator();
            List<String> validationErrors = validator.validateFile(inputFile);

            if (validationErrors == null) { // Pass validation
                // check estimatedProcessingTime.
                rm.setStatus("pass");
                SoccerServiceHelper soccerHelper = new SoccerServiceHelper(strOutputDir);
                Double estimatedTime = soccerHelper.getEstimatedTime(absoluteInputFileName);
                rm.setEstimatedTime(String.valueOf(estimatedTime));
                if (estimatedTime > estimatedThreshhold) { // STATUS: QUEUE (Ask client for email)
                    // Construct Response String in JSON format.
                    rm.setStatus("queue");
                } else { // STATUS: PASS (Ask client to confirm calculate)
                    // all good. Process the output and Go to result page directly.
                    rm.setStatus("pass");
                }
            } else {  // STATUS: FAIL // Did not pass validation.
                // Construct Response String in JSON format.
                rm.setStatus("invalid");
                rm.setDetails(validationErrors);
            }

        } catch (IOException e) {
            LOGGER.log(Level.SEVERE, "FileUploadException or FileNotFoundException. Error Message: {0}", new Object[]{e.getMessage()});
            rm.setStatus("fail");
            rm.setErrorMessage("Oops! We met with problems when uploading your file. Error Message: " + e.getMessage());
        }

        // Send the response.
        String response = "";
        ObjectMapper jsonMapper = new ObjectMapper();
        try {
            LOGGER.log(Level.INFO, "Response: {0}", new Object[]{jsonMapper.writeValueAsString(rm)});

            // Generate metadata file
            response = jsonMapper.writeValueAsString(rm);
            new MetadataFileUtil(rm.getInputFileId(), repositoryPath).generateMetadataFile(response);

        } catch (IOException ioe) {
            response = "";
        }

        // write response to file
        try (FileWriter file = new FileWriter(absoluteInputFileName + "_response.json")) {
            file.write(response);
        } catch (IOException e) {
            e.printStackTrace();
        }

        // Response to the client.
        return response;

    }

}
