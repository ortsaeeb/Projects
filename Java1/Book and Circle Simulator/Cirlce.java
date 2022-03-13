/*
 *File name: Cirlce.java
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
public class Cirlce
{
 
	 
	
	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);
		
		System.out.println("Enter radius of circle");
		double radius = scan.nextDouble();
		
		
		
	  CircleDriver circleojb = new CircleDriver(radius);
	 
	  
	  System.out.println("Area =" + CircleDriver.getArea());
	  System.out.println("Diameter =" + CircleDriver.getDiameter());
	  System.out.print("Circumference =" + CircleDriver.getCircumference());
	  
		scan.close();

	}

}
