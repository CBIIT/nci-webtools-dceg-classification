/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gov.nih.nci.soccer;

import gov.nih.nci.queue.utils.PropertiesUtil;
import java.io.*;
import java.util.logging.*;

/**
 *
 * @author wangy21
 */
public class SoccerRHelper {
    private final static Logger LOGGER = Logger.getLogger(SoccerRHelper.class.getCanonicalName());

    private final String outputDir;
    final String rFunctionFile = PropertiesUtil.getProperty("gov.nih.cit.soccer.r.file").trim();
    final String rScript = PropertiesUtil.getProperty("gov.nih.cit.soccer.rscript").trim();

    public SoccerRHelper(String outputDir) {
        this.outputDir = outputDir;
    }

    /*
     * soccerResultFileId: "o5b659690-f611-4d17-9809-16a3bbea0ba6.csv";
     */
    public boolean generatePlotImg(String soccerResultFileId) {
        String sOutputFile = outputDir  + File.separator +  soccerResultFileId;
        String sPlotOutputImgFile = outputDir  + File.separator + soccerResultFileId + ".png";

        LOGGER.log(Level.INFO, "\r\n-- R Function file: {0} \r\n--SoccerResultFile: {1} \r\n--ImageFile: {2}, \r\n--rScript: {3}", new Object[]{rFunctionFile, sOutputFile, sPlotOutputImgFile, rScript});

        // Check required files.
        if(!(new File(rFunctionFile).exists() && new File(sOutputFile).exists() && new File(rScript).exists())) {
            LOGGER.log(Level.SEVERE, "{0} or {1} or {2} does not exsit.", new Object[]{rFunctionFile, sOutputFile, rScript});
            return false;
        }

        // Run the R script.
        String commandFull;
        commandFull = new StringBuilder(rScript).append(" ")
                .append(rFunctionFile).append(" ")
                .append(sOutputFile).append(" ")
                .append(sPlotOutputImgFile).toString();
        LOGGER.log(Level.INFO, commandFull);
        return ExeCommand(commandFull);
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
}


