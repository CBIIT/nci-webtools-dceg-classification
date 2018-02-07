package gov.nih.nci.queue.api;

import gov.nih.cit.soccer.input.SOCcerException;
import gov.nih.nci.queue.model.ResponseModel;
import gov.nih.nci.queue.utils.MetadataFileUtil;
import gov.nih.nci.queue.utils.PropertiesUtil;
import gov.nih.nci.queue.utils.UniqueIdUtil;
import gov.nih.nci.soccer.SoccerRHelper;
import gov.nih.nci.soccer.SoccerServiceHelper;
import org.codehaus.jackson.map.ObjectMapper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Created by yankovsr on 4/12/2017.
 */
public class FileCalculate {

    private static final long serialVersionUID = 1736940320783327251L;
    private static final Logger LOGGER = Logger.getLogger(FileCalculate.class.getCanonicalName());

    public static void main(String[] args) {
        // Set response type to json
//        PrintWriter writer = response.getWriter();

        String inputFileId = args[0];
        FileCalculate fc = new FileCalculate();
        fc.calculate(inputFileId);
    }


    private String calculate(final String inputFileId) {

        // Get parameters.
        final String repositoryPath = PropertiesUtil.getProperty("gov.nih.nci.queue.repository.dir").trim();
        final String strOutputDir = PropertiesUtil.getProperty("gov.nih.cit.soccer.output.dir").trim();
        System.setProperty("gov.nih.cit.soccer.output.dir", strOutputDir);
        System.setProperty("gov.nih.cit.soccer.wordnet.dir", PropertiesUtil.getProperty("gov.nih.cit.soccer.wordnet.dir").trim());
        if (System.getProperty("gov.nih.cit.soccer.output.dir", "na").equals("na")
                || System.getProperty("gov.nih.cit.soccer.wordnet.dir", "na").equals("na")) {
            LOGGER.log(Level.SEVERE, "Internal Error: Cannot find system variables.");
//            writer.print("Internal Error: Cannot find system variables. Please contact Technical Support.");
        }
        // get input fileId
//        final String inputFileId = request.getParameter("inputFileId");
        String absoluteInputFileName = repositoryPath + File.separator + inputFileId;
        LOGGER.log(Level.INFO, "AbsoluteInputFileName: {0}, output.dir: {1}", new Object[]{absoluteInputFileName, strOutputDir});

        // Process the file.
        LOGGER.log(Level.INFO, "Start processing input file <{0}>.", new Object[]{absoluteInputFileName});
        // all good. Prepare the json output.
        
        ObjectMapper rmMapper = new ObjectMapper();
        String existingMetaData = new MetadataFileUtil(inputFileId, repositoryPath).getMetaExistingMetadata();
        ResponseModel rm = rmMapper.readValue(existingMetaData, ResponseModel.class);

        // ResponseModel rm = new ResponseModel();
        // rm.setInputFileId(inputFileId);
        // File inputFile = new File(absoluteInputFileName);
        // String fileName = originalFileName;
        // rm.setFileName(fileName);
        // long sizeInBytes = inputFile.length();
        // rm.setFileSize(String.valueOf(sizeInBytes));
        // String inputFileId = inputFile.getName();
        // rm.setInputFileId(inputFileId);
        // rm.setFileType("application/vnd.ms-excel");
        // SoccerServiceHelper soccerHelper = new SoccerServiceHelper(strOutputDir);
        // Double estimatedTime = soccerHelper.getEstimatedTime(absoluteInputFileName);
        // rm.setEstimatedTime(String.valueOf(estimatedTime));

        String outputFileId = inputFileId;
        String absoluteOutputFileName = repositoryPath + File.separator + outputFileId;
        try {
            SoccerServiceHelper ssh = new SoccerServiceHelper(strOutputDir);
            ssh.ProcessingFile(new File(absoluteInputFileName), new File(absoluteOutputFileName));

            SoccerRHelper srh = new SoccerRHelper(repositoryPath);
            if(srh.generatePlotImg(outputFileId)) {
                // all good. Prepare the json output.
                LOGGER.log(Level.INFO, "The output file <{0}> has been generated successfully.", absoluteOutputFileName);
                rm.setStatus("pass");
                rm.setOutputFileId(outputFileId);
            } else {
                rm.setStatus("fail");
                LOGGER.log(Level.SEVERE, "R function failed. Error Message: {0}.png does not exist!", absoluteOutputFileName);
            }
        } catch (IOException | SOCcerException e) {
            rm.setStatus("fail");
            rm.setErrorMessage(e.getMessage());
            LOGGER.log(Level.SEVERE, "Failed to generate output file <{0}>. Error Message: {1}", new Object[]{absoluteOutputFileName, e.getMessage()});
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
