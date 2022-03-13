/*
 *File name: Hw1.java
 *
 *Programmer: Samson Okunola
 *
 *
 *Date:Sep 3, 2019
 *
 *Class: IT 168
 *Lecture Section: 01
 *Lecture Instructor: Qi Zhang
 *Lab Section: 03
 *Lab Instructor: Toba Adegbite
 */
package edu.ilstu;

import java.util.Scanner;

/**
 *<insert class description here>
 *
 * @author Samson
 *
 */
public class Hw1
{
	public static final double PI = 3.14;
	public static final double GALLONS = 7.48;		
	//set up constants for calculations in program

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
	Scanner scan = new Scanner(System.in );
		
		System.out.print("Please state the width of the sphere in inches:");
		double width = scan.nextDouble();
		double radius = width / 2;
		//input from the user and establishing the radius variable
		
		double area = 4 * PI * Math.pow(radius,2); 		
		System.out.printf("Area in inches: %,.2f%n",area);
		//calculation for area then output for area
		
		double area2 = area/144;		
		System.out.printf("Area of sphere in feet: %,.2f%n", area2);
		//calculation for area2 then output for area2
		
		double volume = 1.3333333333 * PI * Math.pow(radius, 3);
		System.out.printf("Volume of the sphere in inches is: %,.2f%n", volume );
		//calculation for volume and the volume output
		
		double volume2 = volume/1728;
		System.out.printf("Volume of sphere in feet: %,.2f%n" , volume2);
		//calculation for volume2 and its output
		
		double liquid = volume2 * GALLONS;	
		System.out.printf("The sphere holds this many gallons of water: %,.2f%n ", liquid);
        //calculation for liquid and its own output
	}

}
