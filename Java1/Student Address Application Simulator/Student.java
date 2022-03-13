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

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Student
{
	private static final int NUMBER_OF_ASSIGNEMNETS = 5;
	private static final int 	NUMBER_OF_EXAMS = 2;
	private int studentID;
	private String firstName;
	private String lastName;
	private Address address;
	private double [] assignmentGrade= new double[NUMBER_OF_ASSIGNEMNETS];
	private double [] examGrades= new double[NUMBER_OF_EXAMS];
	private double  totalGradeAverage;
	
	
	public Student (int studentID, String firstName, String lastName, Address address )
	{
		this.studentID = studentID;
		this.firstName = firstName;
		this.lastName = lastName;
		this.address = address;
	}
	public int getStudentID()
	{
		return studentID;
	}


	public String getFirstName()
	{
		return firstName;
	}


	public String getLastName()
	{
		return lastName;
	}



	public Address getAddress()
	{
		return this.address;
	}



	public double[] getArrayAssignmentGrade()
	{
		return assignmentGrade;
	}


	public void setAssignmentGrade(double [] arrayAssignmentGrade)
	{
		this.assignmentGrade = arrayAssignmentGrade;
	}


	public double [] getExamGrades()
	{
		return examGrades;
	}


	public void setAxamGrades(double [] examGrades)
	{
		this.examGrades = examGrades;
	}


	public static int getNumberOfAssignemnets()
	{
		return NUMBER_OF_ASSIGNEMNETS;
	}


	public static int getNumberOfExams()
	{
		return NUMBER_OF_EXAMS;
	}
	public double calculateAssignment()
	{
		int total=0;
		for(int i=0; i<assignmentGrade.length;i++) {
			total+=assignmentGrade[i];
		}
		return total;
	}
	
	public double examAverage()
	{
		int total=0;
		int avg=0;
		for(int i=0; i<examGrades.length;i++) {
			total+=examGrades[i];
		}
		avg= total/NUMBER_OF_EXAMS;
		
		return avg;
	}
	
	public double totalGrade()
	{
		double totalGradeAverage = calculateAssignment()+examAverage();
		return totalGradeAverage;
				
	}
	@Override
	public String toString()
	{
		return "StudentID" + studentID +
				" \nStudent Name: " + firstName+ " "+lastName + 
				" \nAssignment Total:"+ calculateAssignment()+
				" \nExam Average:" + examAverage()+ 
				" \nTotal Grade0: " + totalGrade();
	}
		
	
	

	
	
}
