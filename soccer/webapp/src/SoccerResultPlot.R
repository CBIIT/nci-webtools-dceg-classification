#SoccerResultPlot.R
options(echo=TRUE) # if you want see commands in output file
args <- commandArgs(trailingOnly = TRUE)
print(args)
# trailingOnly=TRUE means that only your arguments are returned, check:
# print(commandsArgs(trailingOnly=FALSE))

soccer_result_file <- args[1]
plot_output_img_file <- args[2]
rm(args)

soccerResultPlot<-function(soccerResultsFile, plotOutputImgFile, breaks=seq(-0.005,1.005,0.01),...){
  png(plotOutputImgFile);


  opar<-par(no.readonly=T);
  soccerResults<-read.csv(soccerResultsFile,stringsAsFactor=F)
  tie<-(soccerResults$Prob1== soccerResults$Prob2);
  t<-table(ifelse(tie,"Yes","No"),dnn="Tie")
	
  h<-hist(soccerResults$Prob1[!tie],breaks=seq(-0.01,1.01,0.02),plot=F)
  par(mfcol=c(2,1),omi=rep(0,4),mgp=c(2,1,0),mar=c(3,3,1,2))
  plot(h$mids,cumsum(h$counts)/sum(h$counts),xlim=c(0,1),ylim=c(0,1),xlab="SOCcer score (Unique Results)",ylab="score CDF",...)
  text(0.0,0.85, paste(capture.output(t), collapse='\n'), pos=4 , cex=0.8)
  text(0.4,0.05, paste(capture.output(summary(soccerResults$Prob1[!tie])), collapse='\n'), pos=4 , family="mono",cex=0.7)

  h<-hist(soccerResults$Prob1[tie],breaks=seq(-0.01,1.01,0.02),plot=F)
  plot(h$mids,cumsum(h$counts)/sum(h$counts),xlim=c(0,1),ylim=c(0,1),xlab="SOCcer score (Tie)",ylab="score CDF",...)
  text(0.4,0.05, paste(capture.output(summary(soccerResults$Prob1[tie])), collapse='\n'), pos=4 , family="mono",cex=0.7)
  par(opar)  
  invisible(dev.off())
}

soccerResultPlot(soccer_result_file, plot_output_img_file);
