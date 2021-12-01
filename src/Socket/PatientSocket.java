/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Socket;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author macbookair
 */
public class PatientSocket {

    /**
     * @param args the command line arguments
     */
    public PatientSocket() {

    }

    public void sendFile(File file) throws IOException, InterruptedException {

        Socket socket = null;

        socket = new Socket("localhost", 9000);

        // Get the size of the file
        long length = file.length();
        byte[] bytes = new byte[16 * 1024];
        InputStream in = new FileInputStream(file);
        OutputStream out = socket.getOutputStream();

        int count;
        while ((count = in.read(bytes)) > 0) {
            out.write(bytes, 0, count);
            Thread.sleep(30000);
        }

        releaseResources(out, in, socket);

    }

    public boolean sendUserPassword(String dni, String password) throws IOException {
        boolean right = false;

        Socket socket = null;

        socket = new Socket("localhost", 9000);

        PrintWriter printWriter = new PrintWriter(socket.getOutputStream(), true);
        printWriter.println(dni);
        printWriter.println(password);

        //recibir ok por parte del servidor
        System.out.println("hola soy el cliente y voy a recibit el ok del server");
        BufferedReader bufferedReader = null;

        String ok = null;

        try {
            bufferedReader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
        } catch (IOException ex) {
            Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);
        }
        String line;
        try {
            ok = bufferedReader.readLine();
            System.out.println("El msg del server es:" + ok);
            if (ok.equals("true")) {
                return true;
            } else {
                return false;
            }

        } catch (IOException ex) {
            Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);
        }
        releaseResources(bufferedReader, printWriter, socket);
        return right;
    }

    private static void releaseResources(OutputStream outputStream,
            InputStream console, Socket socket) {
        try {

            try {
                console.close();
            } catch (IOException ex) {
                Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);

            }

            try {
                outputStream.close();
            } catch (IOException ex) {
                Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);

            }

            socket.close();

        } catch (IOException ex) {
            Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);
        }

    }

    private static void releaseResources(BufferedReader b, PrintWriter printWriter, Socket socket) {
        try {
            b.close();
            printWriter.close();
            socket.close();
        } catch (IOException ex) {
            Logger.getLogger(PatientSocket.class.getName()).log(Level.SEVERE, null, ex);
        }
    }
}
