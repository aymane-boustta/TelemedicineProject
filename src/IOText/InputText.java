/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package IOText;

import Bitalino.Frame;
import Pojos.Patient;
import java.io.*;

/**
 *
 * @author diego
 */
public class InputText {

    public InputText() {
    }

    //Metodo para escribir Patient en .txt
    public void inputPatientDataText(Patient patient) {

        FileWriter file = null;
        PrintWriter pw = null;

        //check if the directory of the patient exists
        File carpeta = new File("PatientsDB/" + patient.getName());
        if (carpeta.exists()) {
            System.out.println("Patient is already in the DB");
        } else {
            try {
                File newCarpeta = new File("PatientsDB/" + patient.getName());
                newCarpeta.mkdir();
                file = new FileWriter("PatientsDB/" + patient.getName() + "/" + patient.getName() + ".txt");
                pw = new PrintWriter(file);

                pw.println(patient.getName());//name
                pw.println(patient.getSurname());//surname
                pw.println(patient.getDob());//dob
                pw.println(patient.getAddress());//address
                pw.println(patient.getEmail());//email
                pw.println(patient.getAge());//age
                pw.println(patient.getSexe());//sex

                // lo envio en un socket que recibo como parametro.
            } catch (IOException ex) {
                ex.printStackTrace();
            } finally {
                try {
                    file.close();
                } catch (IOException ex) {
                    ex.printStackTrace();
                }
            }
        }
    }

    //Metodo para escribir las señales bitalino en el .txt (UNA SEÑAL POR FICHERO)
    public void inputBitalinoDataText(Frame[] frame) {
        FileWriter file = null;
        PrintWriter pw = null;

        try {
            file = new FileWriter("PatientsDB/signal.txt", true);
            pw = new PrintWriter(file);
            for (int i = 0; i < frame.length; i++) {
                System.out.println(String.valueOf(frame[i].analog[0]));
                pw.println(String.valueOf(frame[i].analog[0]));
            }
        } catch (IOException ex) {
            ex.printStackTrace();
        } finally {
            try {
                file.close();
            } catch (IOException ex) {
                ex.printStackTrace();
            }
        }
    }
}