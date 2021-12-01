package Bitalino;

import IOText.InputText;
import Socket.PatientSocket;
import java.io.*;
import java.util.Vector;
import javax.bluetooth.RemoteDevice;

public class BitalinoDemo {

    public static Frame[] frame;
    public static InputText inputText = new InputText();

    public String startRecording() {
        PatientSocket patientSocket = null;
        BITalino bitalino = null;
        FileWriter fileWriter = null;

        PrintWriter pw = null;
        try {
            bitalino = new BITalino();

            fileWriter = new FileWriter("PatientsDB/signalprueba.txt");

            pw = new PrintWriter(fileWriter);

            // Code to find Devices
            //Only works on some OS
            Vector<RemoteDevice> devices = bitalino.findDevices();
            System.out.println(devices);

            //You need TO CHANGE THE MAC ADDRESS
            //You should have the MAC ADDRESS in a sticker in the Bitalino
            String macAddress = "98:D3:51:FD:9C:72";

            //Sampling rate, should be 10, 100 or 1000
            int SamplingRate = 10;
            bitalino.open(macAddress, SamplingRate);

            // Start acquisition on analog channels A2 and A6
            // For example, If you want A1, A3 and A4 you should use {0,2,3}
            int[] channelsToAcquire = {1};
            bitalino.start(channelsToAcquire);

            //Read in total 10000000 times
            for (int j = 0; j < 50; j++) {

                //Each time read a block of 10 samples
                int block_size = 10;
                frame = bitalino.read(block_size);

                //Print the samples
                for (int i = 0; i < frame.length; i++) {
                    //System.out.println((j * block_size + i) + " seq: " + frame[i].seq + " "
                    //       + frame[i].analog[0] + " "
                    //        + frame[i].analog[1] + " "
                    //  + frame[i].analog[2] + " "
                    //  + frame[i].analog[3] + " "
                    //  + frame[i].analog[4] + " "
                    //  + frame[i].analog[5]
                    //);
                    pw.println(frame[i].analog[0]);
                }

            }

            //stop acquisition
            bitalino.stop();
        } catch (BITalinoException ex) {
            return "Something has gone wrong";
        } catch (Throwable ex) {
            return "Something has gone wrong";
        } finally {
            try {
                //close bluetooth connection
                if (bitalino != null) {
                    bitalino.close();
                }

            } catch (BITalinoException ex) {
                return "Something has gone wrong";
            }
            try {
                fileWriter.close();
                String msg = sendFile();
                return msg;
            } catch (IOException ex) {
                return "Something has gone wrong";

            }
        }
    }

    public String sendFile() {
        PatientSocket patientSocket = new PatientSocket();
        File file = new File("PatientsDB/signalprueba.txt");
        try {
            patientSocket.sendFile(file);
        } catch (IOException ex) {
            return "Something has gone wrong";
        } catch (InterruptedException ex) {
            return "Something has gone wrong";
        }
        return "The information has been recorded and sent to the doctor correctly";
    }
}
