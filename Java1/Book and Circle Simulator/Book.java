/*
 *File name: Book.java
 *
 *Programmer: Samson Okunola
 *
 *Date:Sep 17, 2019
 *
 *Class: IT 168
 *Lecture Section: 01
 *Lecture Instructor: Qi Zhang
 *Lab Section: 03
 *Lab Instructor: Toba Adegbite
 */
package edu.iltstu;

import java.util.Scanner;

/**
 *<insert class description here>
 *
 * @author Samson
 *
 */
public class Book
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		
		
		Scanner scan = new Scanner(System.in);
		System.out.println("How many Life of PI were sold");
		int num1 = scan.nextInt();
		BookDriver book1 = new BookDriver("Life of PI", 13.50 , num1);
		System.out.println("Cost of Life of PI = $" + book1.getCalculateSales(13.50,num1));
		
		
		System.out.println("How many Harry Potter and the Goblet of fire were sold");
		int num2 = scan.nextInt();
		BookDriver book2 = new BookDriver("Harry Potter and the Goblet of Fire", 22.00, num2);
		System.out.println("Cost of Harry Potter and the Goblet of fire = $"+  book2.getCalculateSales(22.00, num2));
		
		
		System.out.println("Enter percent increase of price for Life of PI");
		double num3 = scan.nextDouble();
		num3 = book2.getPrice() * num3;
		num3 = book2.getPrice() + num3;
		
	
				
		
		System.out.println("Enter percent increase of price for Harry Potter and the Goblet of Fire");
		double num4 = scan.nextDouble();
		num4 = book1.getPrice() * num4;
		num4 = num4 +book1.getPrice();
		
		System.out.println("Cost of Life of PI=$" + num3);
		
		System.out.println("Cost of Harry Potter and the Goblet Of Fire=$" + num4);
		
		
}
}