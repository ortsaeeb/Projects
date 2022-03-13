/*
*File name: OECDApp.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Apr 28, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;

import java.util.Scanner;

import jdk.nashorn.internal.runtime.regexp.joni.exception.InternalException;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class OECDApp
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);
		OECDHandler oe = new OECDHandler(null);
		oe.read("oecd_bli.cvs");
		 
		int options;
		
		
		do
		{
			menu();
			System.out.println("Please make your Choice");
			
			try
			{
				options = Integer.parseInt(scan.next());
						while(options>7||options<1)
						{
							System.out.println("Please try again");
							options = Integer.parseInt(scan.next());
						}
			  } catch (NumberFormatException e) {
	               options = 0;
	               System.out.println("Please input a number between 1 and 5!");
	           }

	           switch (options) {
	           case 1: {
	        	   System.out.print("Country\t\t\t\t"+"Employment Rate\t\t\t\t"+"Job Security\t\t\t\t"+"Life Expectancy\t\t\t\t"+"Personal Earnings\n");
	               oe.displayAllCountries();
	               break;
	           }
	           case 2: {
	               System.out.println("Please input a country's name: ");
	               oe.searchName(scan.next());
	               break;
	           }
	           case 3: {
	               System.out.println("Please give an employment rate: ");
	               try {
	                   oe.searchByEmploymentRatee(scan.nextInt());
	               } catch (InternalException e) {
	                   System.out.println("Please type an integer!");
	                  
	               }
	               break;
	           }
	           case 4: {
	               oe.rankCountriesByEarnings();
	               System.out.println("Successful!");
	               break;
	           }
	           case 5: {
	               System.out.println("Thank You for using the database.Please come back next time.");
	               break;
	           }
	           }
	       } while (options != 5);

	   }
						
						
			
			
		

		public static void menu() {
		       System.out.println(" Welcome to the OECD Database ");
		       System.out.println("====================================");
		       System.out.println("1. Browse all countries.");
		       System.out.println("2. Search for a country.");
		       System.out.println("3. Search for countries based on employment rate.");
		       System.out.println("4. Rank countries by personal earnings.");
		       System.out.println("5. Exit.");
		       System.out.println("====================================");
		   
		
		
		
		

	}

}
