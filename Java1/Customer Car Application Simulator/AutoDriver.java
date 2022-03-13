/*
*File name: AutoDriver.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Jul 29, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Tonya Pierce
*Lab Section: 1
*Lab Instructor: Reki Puri
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
public class AutoDriver
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);

		InputOutput io = new InputOutput();
		Inventory inventory = new Inventory();
		

				
		int size = io.readInventory(inventory.getInventory());
		inventory.setSize(size);
		
		// start menu logic 
		
		       
		       int options;
		       

				do
				{
					menu();
					System.out.println("Please make your Choice:");
						
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
			               System.out.println("Please input a number between 1 and 7!");
			           }

			           switch (options) {
			           case 1: {
			        	   System.out.print("Year\t\t\t\t"+"Make \t\t\t\t"+"Model \t\t\t\t"+"Price\t\t\t\t"+"Condition"+"Rating\t\t\t\t\t+Status\t\t\t\t\t"+"Vin\n");
			        	  inventory.EntireInventory();
			               break;
			           }
			           case 2: {
			               System.out.println("Display the entire automobile inventory sorted by year");
			               inventory.sortbyYear();
			               break;
			           }
			           case 3: {
			           
			        	   System.out.print("Year\t\t\t\t"+"Make \t\t\t\t"+"Model \t\t\t\t"+"Price\t\t\t\t"+"Condition"+"Rating\t\t\t\t\t+Status\t\t\t\t\t"+"Vin\n");
			        	  inventory.displayAvailableInventory();
			               break;
			              
			           }
			           
			           case 4: {
			        	   System.out.println("Display the entire automobile inventory sorted by year");
			               inventory.displaySoldInventory();
			               break;
			           }
			           case 5: {
			        	   System.out.println("Buyers Mail List");
			               inventory.displayBuyersMailList();
			               
			               break;
			           }
			           case 6: {
			        	   System.out.println("Find automobile by VIN number: ");
			               try {
			            	   inventory.findExactVehicle(null);
			               } catch (InternalException e) {
			                   System.out.println(" ");
			                  
			               
			               break;
			               }
			           }
			           
			          
			           case 7: {
			               System.out.println("Thank You for using the database.Please come back next time.");
			               break;
			           }
			           }
			       } while (options != 7);

			   }
				
				
				
// while
// switch


	public static  void menu() {
	       System.out.println(" Specialty Auto ");
	       System.out.println("(1)Display the entire automobile inventory list");
	       System.out.println("(2)Display the entire automobile inventory sorted by year");
	       System.out.println("(3) Display automobiles available for sale");
	       System.out.println("(4) Display list of recently sold automobiles");
	       System.out.println("(5) Output a mailing list of recent buyers");
	       System.out.println("(6) Find automobile by VIN number");
	       System.out.println("(7) Quit");
	}

	
	
}
