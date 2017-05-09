/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package gov.nih.nci.queue.utils;

import gov.nih.nci.queue.model.QueueModel;
import org.codehaus.jackson.map.ObjectMapper;

import javax.jms.*;
import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import java.io.IOException;
import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Yutao
 */
public class QueueProducerUtil {
    private final static Logger LOGGER = Logger.getLogger(QueueProducerUtil.class.getCanonicalName());

    private Context context;
    private Queue fileQueue;
    private ConnectionFactory connectionFactory;

    private final String CONNECTION_FACTORY_JNDI;
    private final String QUEUE_JNDI;
    public QueueProducerUtil() {
        CONNECTION_FACTORY_JNDI = new StringBuilder("openejb:Resource/")
                .append(PropertiesUtil.getProperty("resource.queue.connectionfactory").trim())
                .toString();
        QUEUE_JNDI = new StringBuilder("openejb:Resource/")
                .append(PropertiesUtil.getProperty("resource.queue.name").trim())
                .toString();
    }

    /*
     * Add message into Queue.
     */
    public void sendToQueue(QueueModel qm) throws NamingException, JMSException, IOException {

        context = new InitialContext();
        connectionFactory = (ConnectionFactory) context.lookup(CONNECTION_FACTORY_JNDI);
        fileQueue = (Queue) context.lookup(QUEUE_JNDI);

        // Connect to Queue.
        Connection connection = connectionFactory.createConnection();
        connection.start();

        // Create a Session and set auto acknowledge.
        Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);

        // Create a MessageProducer from the Session to the Topic or Queue
        MessageProducer producer = session.createProducer(fileQueue);
        producer.setDeliveryMode(DeliveryMode.PERSISTENT);

        // Add timestamp and create a json message
        ObjectMapper jsonMapper = new ObjectMapper();
        qm.setTimeStamp(new Date() + "");
        LOGGER.log(Level.INFO, "Response: {0}", new Object[]{jsonMapper.writeValueAsString(qm)});
        TextMessage message = session.createTextMessage(jsonMapper.writeValueAsString(qm));

        // Tell the producer to send the message
        producer.send(message);

        // close all.
        producer.close();
        session.close();
        connection.close();
    }
}
