package gov.nih.nci.queue.api;

import gov.nih.nci.queue.model.QueueModel;
import gov.nih.nci.queue.model.ResponseModel;
import gov.nih.nci.queue.utils.MetadataFileUtil;
import gov.nih.nci.queue.utils.PropertiesUtil;
import gov.nih.nci.queue.utils.QueueProducerUtil;
import org.codehaus.jackson.map.ObjectMapper;

import javax.jms.JMSException;
import javax.naming.NamingException;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Created by yankovsr on 4/13/2017.
 */
public class FileQueue {
    private static final long serialVersionUID = 8388204653049285309L;
    private static final Logger LOGGER = Logger.getLogger(FileQueue.class.getCanonicalName());

    public static void main(String args[]) {

        String emailAddress = args[0];
        String inputFileId = args[1];

        FileQueue fq = new FileQueue();
        fq.sendToQueue(emailAddress, inputFileId);
    }

    private String sendToQueue(final String emailAddress, final String inputFileId) {

        final String repositoryPath = PropertiesUtil.getProperty("gov.nih.nci.queue.repository.dir").trim();
        final String outputDir = PropertiesUtil.getProperty("gov.nih.cit.soccer.output.dir").trim();
        final String absoluteInputFileName = repositoryPath + File.separator + inputFileId;

        // Send to Queue
        QueueModel qm = new QueueModel();
        qm.setFileName(inputFileId);
        qm.setPath(repositoryPath);
        qm.setEmail(emailAddress);
        qm.setOutputDir(outputDir);
        // Create objects for JSON response.
        ResponseModel rm = new ResponseModel();
        try {
            new QueueProducerUtil().sendToQueue(qm);
            LOGGER.log(Level.INFO, "File <{0}> has been queued. ", new Object[]{inputFileId});

            // all good. Prepare the json output.
            rm.setStatus("pass");
            rm.setEmailAddress(emailAddress);
        } catch (NamingException | JMSException | IOException e) {
            rm.setStatus("fail");
            rm.setErrorMessage(e.getMessage());
        }

        // Store the response.
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
