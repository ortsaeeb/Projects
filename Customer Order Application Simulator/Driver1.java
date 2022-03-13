/*
*File name: Driver1.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Mar 30, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;

import java.util.Random;
import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Driver1
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		startupMenu();

		
	}
		public static Scanner f = new Scanner(System.in);
		public static Order order;
	
		
		public static void outputResults(Order newOrder, Customer customer)
		{
			Summary sum = new Summary();
			sum.calculateSubbTotal(order);
			sum.calculateNewTax(order);
			sum.calculateTotal(order);
			System.out.println(customer.toString()+
					"\n"+order.toString()+
					"\n" +"Order Summary: "+
					sum.outputNewSummary(order));
		}
		public static void getCustomerInfo(int newDeliver, Order order)
		{
			Customer custom;
			if(newDeliver==0)
			{
				System.out.print("\nEnter your name: ");
				String name = f.next();
				System.out.print("\nEnter your name: ");
				String phoneNumber = f.next();
			
			custom = new Customer( name , null , phoneNumber);
			}	
			else
			{
				System.out.print("\nEnter your name: ");
				String name = f.next();
				System.out.print("\nEnter your Phone Number: ");
				String phoneNumber = f.next();
				System.out.print("\nEnter your Address: ");
				String address = f.next();
	custom = new Customer(name, address, phoneNumber);
			
			Random rand = new Random();
			System.out.println("The deliver time is "+(rand.nextInt(60-30)+30)+"minutes");
			}
			outputResults(order, custom);
		}
		public static int determineDelivery()
		{
			System.out.println("\nPress 1 for pickup");
			System.out.println("Press '1' for Delivery");
			int option = f.nextInt();
			return option;
		}
		public static void displayMenu()
		{
			Scanner scan = new Scanner(System.in);
			 
			System.out.print("\nHow many Burgers you want? ");
			System.out.print("\nHow many Fries you want? ");
			System.out.print("\nHow many Tacos you want? ");
			System.out.print("\nHow many Chicken SandWich you want? ");
			System.out.print("\nHow many Nachos you want? ");
			//-------------------------------------------------------------------------
			System.out.println("\n1- Burger");
			int burger = f.nextInt();
			System.out.println("2-   Fries");
			int fries = f.nextInt();
			System.out.println("3-   Taco ");
			int taco = f.nextInt();
			System.out.println("4-   Chicken SandWich");
			int chicken = f.nextInt();
			System.out.println("5-   Nachos");
			int nacho = f.nextInt();
			
			boolean isDeliver = false;
			int deliverD = determineDelivery();
			
			if(deliverD==1)
			{
				isDeliver = true;
			}
			order = new Order(burger, fries, taco, nacho, chicken, isDeliver);
			
			getCustomerInfo(deliverD,order);
		}
		public static void drinkMenu()
		{
			System.out.println("How many Small Drinks? ");
			int smallD = f.nextInt();
			System.out.println("How many Medium Drinks? ");
			int mediumD = f.nextInt();
			System.out.println("How many Large Drinks? ");
			int largeD = f.nextInt();
			
			
			boolean isDeliver = false;
			int deliver = determineDelivery();
			if(deliver ==1 )
			{
				isDeliver = true;
			}
			order = new Order(smallD,mediumD,largeD,isDeliver);
			
			getCustomerInfo(deliver , order);
		}
		public static void endOfDay(Order orderE)
		{
			System.out.println("\nNumber of orders at end of the day: "+order.getCountOrders());
		}
		
		public static void startupMenu()
		{
			Scanner f = new Scanner(System.in);
			int option = 0;
			while(!(option==3))
			{
				System.out.println("Which Menu would you like to start with");
				System.out.println("\nFoodMenu");
				System.out.println("2.Drink/sizes menu");
				System.out.println("3.Close");
				
				option = f.nextInt();
				
				if(option ==1)
				{
					displayMenu();
				}
				else if(option==2)
				{
					drinkMenu();
				}
				else if(option ==3)
				{
					endOfDay(order);
				}
			}
			
			
			startupMenu();
		
			
			
		
			
		}}
	



		
		

	


	


