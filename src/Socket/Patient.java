/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Socket;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author macbookair
 */
public class Patient {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) throws IOException {
        
        String fileName;
        
        int byteRead;
        Socket socket = new Socket("localhost", 9000);
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        System.out.println("Introduce the name of file you want to send to the doctor");
        fileName = reader.readLine();
        fileName.toLowerCase();
        byte [] bytes = new byte[(int) fileName.length()];
        InputStream in = new FileInputStream(fileName);
        OutputStream out = socket.getOutputStream();
        while((byteRead = in.read(bytes)) > 0){
            out.write(bytes, 0, byteRead);
        }
        releaseResources(out, in, socket);
        
        

    }
    private static void releaseResources(OutputStream outputStream,
            InputStream console, Socket socket) {
        try {
            try {
                console.close();
            } catch (IOException ex) {
               Logger.getLogger(Patient.class.getName()).log(Level.SEVERE, null, ex);

            }
            
            try {
                outputStream.close();
            } catch (IOException ex) {
              Logger.getLogger(Patient.class.getName()).log(Level.SEVERE, null, ex);

            }
            
            
            socket.close();
            
        } catch (IOException ex) {
            Logger.getLogger(Patient.class.getName()).log(Level.SEVERE, null, ex);
        }
       
    }

}
