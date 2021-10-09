/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package telemedicine;

import java.io.Serializable;
import java.util.Date;

/**
 *
 * @author macbookair
 */
public class Patient implements Serializable {
    
    private static final long serialVersionUID = -1156840724257282729L;
    private Integer id;
    private Integer name; 
    private Integer surname;
    private Date dob;
    private String address;
    private String email;
    private String medicalHistory;
    private int age;
    private String sexe;
    private Doctor doctor;

    public Patient(Integer id, Integer name, Integer surname, Date dob, String address, String email, String medicalHistory, int age, String sexe, Doctor doctor) {
        this.id = id;
        this.name = name;
        this.surname = surname;
        this.dob = dob;
        this.address = address;
        this.email = email;
        this.medicalHistory = medicalHistory;
        this.age = age;
        this.sexe = sexe;
        this.doctor = doctor;
    }
    
}
