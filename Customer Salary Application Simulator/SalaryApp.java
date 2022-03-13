package SalaryClass;

import java.util.Scanner;
/**
 *Programmer:Samson Okunola
 *
 */

public class SalaryApp {

	public static void main(String[] args) {
		
		// DECLARE all variables
		// INSTANTIATE all objects
		Scanner scan = new Scanner(System.in);
		double hours;
		double payPerHour;
		
		Salary salaryObj = new Salary();
		
		// PROMPT and accept the hours and payPerHour of the package.
		System.out.print("Enter working hours: ");
		hours = scan.nextDouble();
		
		System.out.print("Enter pay per hour: ");
		payPerHour = scan.nextDouble();
		
		// CALL the setter methods to set the hours and 
		// payPerHour of the Package.
		salaryObj.setHours(hours);		
		salaryObj.setPayPerHour(payPerHour);
		
		scan.close();

		// DISPLAY the Package information
		System.out.printf("\nWorking hours: %.2f", salaryObj.getHours());
		System.out.printf("\nPay per hour: $%.2f", salaryObj.getPayPerHour());
		System.out.printf("\nShipment Cost: $%.2f", salaryObj.calcSalary());
	}

}

