/*
*File name: dw.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Aug 7, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Tonya Pierce
*Lab Section: 1
*Lab Instructor: Reki Puri
*/
package edu.ilstu;
import java.util.Scanner;
/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class StudentApp
{

	/**
	 * @param args
	 */
	static Address addy;
	static Student stu;
	static Address addy1;
	static Student stu1;
	static Address addy2;
	static Student stu2;
	public static void main(String[] args)
	{
		
		
		 addy = new Address (123,"Jackson","Chicago","IL ",55555);
		 stu = new Student(12,"Adam","Burks",addy);
		
		
		 addy1 = new Address (223,"isu","Normal","IL ",44444);
		 stu1 = new Student(13,"John","Jacob",addy);

		 addy2 = new Address (445,"bloom","Evanston","IL ",66666);
		stu2 = new Student(16,"Sam","ok",addy);
		
		System.out.println("\nWelcome to our Student Management System");
		System.out.println("\n****************************************");
		System.out.println("\n****************************************");
		
		Scanner scan = new Scanner(System.in);
		int input =0;
		int studentID=0;
		while(input!=5) {
			menu();
			input= scan.nextInt();
			if(input==1) {
				displayAllStudents();
			}
			
			if(input==2) {
				System.out.println("Please enter the student ID: ");
				studentID= scan.nextInt();
				addGrades(studentID,scan);
			}
			if(input==3) {
				System.out.println("Please enter the student ID: ");
				studentID= scan.nextInt();
				reportCard(studentID);
				
			}
			if(input==4) {
				System.out.println("Please enter the student ID: ");
				studentID= scan.nextInt();
				displayAddress(studentID);
			}
			if(input>5||input<1) {
				System.out.println("Please enter a number beween 1-5");
			}
			
		
	}
		System.out.print("Goodbye");
		scan.close();
	}		

		
		
	
	
	public static void menu()
	{
		Scanner scan = new Scanner(System.in);
		System.out.println("\nPlease select from the options below: ");
		System.out.println("\n1. Display a list of all students");
		System.out.println("\n2. Enter the grades for a student");
		System.out.println("\n3. Display the report card for a student");
		System.out.println("\n4. Display the address of a student");
		System.out.println("\n5. Exit the system");
	



 
	}
	public static void displayAllStudents()
	{
		System.out.println(stu.getStudentID()+ " - "+stu.getFirstName()+" "+stu.getLastName());
		System.out.println(stu1.getStudentID()+ " - "+stu1.getFirstName()+" "+stu1.getLastName());
		System.out.println(stu2.getStudentID()+ " - "+stu2.getFirstName()+" "+stu2.getLastName());
	}
	public static void addGrades(int studentID, Scanner scan)
	{
		
		int assign=0;
		int exam=0;
		double []grades= new double [5] ;
		double [] exams= new double [2];
		if(studentID==1) {
			for(int i=0; i<stu.getNumberOfAssignemnets();i++) {
				System.out.println("Please enter assignment "+(i+1)+": ");
				assign= scan.nextInt();
				grades[i]= assign;
			}
			stu.setAssignmentGrade(grades);
			for(int i=0; i< stu.getNumberOfExams(); i++) {
				System.out.println("Please enter exam "+(i+1)+": ");
				exam= scan.nextInt();
				exams[i]= exam;
			}
			stu.setAxamGrades(exams);
		}
		if(studentID==2) {
			for(int i=0; i<stu1.getNumberOfAssignemnets();i++) {
				System.out.println("Please enter assignment "+(i+1)+": ");
				assign= scan.nextInt();
				grades[i]= assign;
			}
			stu1.setAssignmentGrade(grades);
			for(int i=0; i< stu1.getNumberOfExams(); i++) {
				System.out.println("Please enter exam "+(i+1)+": ");
				exam= scan.nextInt();
				exams[i]= exam;
				//enter grades for the exams
			}
			stu1.setAxamGrades(exams);
		}	
		if(studentID==3) {
			for(int i=0; i<stu2.getNumberOfAssignemnets();i++) {
				System.out.println("Please enter assignment "+(i+1)+": ");
				assign= scan.nextInt();
				grades[i]= assign;
			}
			stu2.setAssignmentGrade(grades);
			for(int i=0; i< stu2.getNumberOfExams(); i++) {
				System.out.println("Please enter exam "+(i+1)+": ");
				exam= scan.nextInt();
				exams[i]=exam;
				//enter grades for the exams
			}
			stu2.setAxamGrades(exams);
		}
		
		
	}
	public static void reportCard(int studentID)
	{
		
		if(studentID==1) {
		System.out.println(stu.toString());	
		}
		if(studentID==2) {
		System.out.println(stu1.toString());		
		}
		if(studentID==3) {
		System.out.println(stu2.toString());		
		}
		
	}
	public static void displayAddress(int studentID)
	{
		if(studentID==1) {
			System.out.println(stu.getAddress().toString());	
			}
			if(studentID==2) {
			System.out.println(stu1.getAddress().toString());		
			}
			if(studentID==3) {
			System.out.println(stu2.getAddress().toString());		
			}
	}
	

		
	

}
