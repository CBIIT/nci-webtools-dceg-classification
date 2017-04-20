/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gov.nih.nci.queue.model;

import java.io.Serializable;

/**
 * The unit added in queue.
 *
 * @author wangy21
 */
public class QueueModel implements Serializable {
    private static final long serialVersionUID = -4920860875752174246L;

    // InputFile for Processing
    private String fileName;
    // Path to the inputfile.
    private String path;
    // Where to save the output file.
    private String outputDir;
    private String email;
    private String timeStamp;

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getTimeStamp() {
        return timeStamp;
    }

    public void setTimeStamp(String timeStamp) {
        this.timeStamp = timeStamp;
    }

    public String getOutputDir() {
        return outputDir;
    }

    public void setOutputDir(String outputDir) {
        this.outputDir = outputDir;
    }
}
