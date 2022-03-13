/**
 * 
 */
package edu.ilstu;

import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Scanner;

/**
 *Programmer:Samson Okunola
 *
 */
public class CarPurchaseApp {

	private static NumberFormat cur = NumberFormat.getCurrencyInstance();
	private static DecimalFormat num = new DecimalFormat("#,##0");
	private static Scanner keyboard;
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// setup variables for run
		keyboard = new java.util.Scanner(System.in);
		CarPurchase myOrder = null;
		
		// Prompt User for Vehicle 
		Car myAuto = selectCar();
		
		if (myAuto != null)
		{
			myOrder = new CarPurchase(myAuto.toString(), myAuto.getPrice());
			System.out.println("You've selected the " + myOrder.getCarDescription());
			System.out.println("");
				
			// Prompt User for ServiceOptions
			selectServiceOptions(myOrder);			

			// Display Auto Sales Order Receipt
			System.out.println(myOrder);
			
		}
		else  // User did not select a vehicle from inventory
		{
			System.out.println("The car you have selected is not in our inventory." );
		}
		
		// teardown objects
		keyboard.close();
		myOrder = null;
		myAuto = null;
	}
	
	private static Car selectCar()
	{
		// Setup Autos
		Car a1 = new Car(2015, "Toyota", "Camry");
		a1.setPrice(15798);
		a1.setMileage(62030);
		
		Car a2 = new Car(2019, "Honda", "Accord");
		a2.setPrice(26600);
		a2.setMileage(21020);

		final String LINE = "\n--------------------------------------------------";
		final String LAYOUT = "\n%-7s%-25s%-8s%10s";
		String msg
			= "Choose Your Car from Inventory:"
			+ "\n"
			+ LINE
			+ String.format(LAYOUT, "id", "Car", "Miles", "Price")
			+ LINE
			+ String.format(LAYOUT, "1", a1, num.format(a1.getMileage()), cur.format(a1.getPrice()))
			+ String.format(LAYOUT, "2", a2, num.format(a2.getMileage()), cur.format(a2.getPrice()))
		;
		System.out.println(msg);

		// Get User Selection
		System.out.print("\nSelect your Car by item # (e.g. 1, 2): ");
		int autoId = keyboard.nextInt();
		System.out.println("");
		
		switch(autoId)
		{
			case 1: 	return a1;
			case 2:		return a2;
			default:	return null;
		}
	}
	
	private static void selectServiceOptions(CarPurchase myOrder)
	{
		String choice;
		
		System.out.println("Protect your purchase with our pre-paid service offerings.");
		System.out.println("");
		
		System.out.print("\tAdd oil change package for "
				+ cur.format(CarPurchase.OIL_CHANGE_PKG) + " (Y or N)? ");
		choice = keyboard.next();
		if (choice.charAt(0) == 'Y' || choice.charAt(0) == 'y')
		{
			myOrder.setOilChangePackage(true);
		}		
				
		System.out.println("");
	}
}



















