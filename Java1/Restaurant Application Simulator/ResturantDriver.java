/*
*File name: ResturantDriver.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Feb 20, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;
import java.text.DecimalFormat;
import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class ResturantDriver
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);
		System.out.println("\tWelcome To the Online Ordering System");
		System.out.println("\nChoose The Number Of Each Entree you wish to order.");
		System.out.println("How many Salmon orders do you want:  ");
		int countSalmon = scan.nextInt();
		System.out.println("How many Chicken orders do you want:  ");
		int countChicken = scan.nextInt();
		System.out.println("How many Steak orders do you want:  ");
		int countSteak = scan.nextInt();
		System.out.println("How many lamb orders do you want:  ");
		int countLamb = scan.nextInt();
		
		System.out.println("Choose the number of each side you wish to order  ");

		System.out.println("How many Fries orders do you want:  ");
		int countFries = scan.nextInt();
		System.out.println("How many Salad orders do you want:  ");
		int countSalad = scan.nextInt();
		System.out.println("---------------------------------------------------");

		System.out.println("You have ordered the Following");
		System.out.println("Salmon:     "+countSalmon);
		System.out.println("Chicken:    "+countChicken);
		System.out.println("Steak:      "+countSteak);
		System.out.println(" Lamb:       "+countLamb);
		System.out.println("Fries:      "+countFries);
		System.out.println("Salad:      "+countSalad);
		System.out.println("---------------------------------------------------");
		TheOrderClass newOrder = new TheOrderClass(countSalmon, countChicken,countSteak, countLamb, countFries, countSalad);

		DecimalFormat df = new DecimalFormat("#.##");
		System.out.println("SubTotal:  $"+ df.format(newOrder.calculateSubTotal()));
		System.out.println("     Tax:  $"+ df.format (newOrder.calculateTax()));
		System.out.println("Service Fee: $"+ df.format(newOrder.calculateServiceCharge()));
		System.out.println("   Total:  $"+ df.format(newOrder.calculateTotalCharge()));


		
		
		
		

		
		
	}

}
