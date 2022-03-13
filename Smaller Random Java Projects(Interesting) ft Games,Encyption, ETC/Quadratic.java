/*
*File name: part2.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Jun 8, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Tonya Pierce
*Lab Section: 1
*Lab Instructor: Reki Puri
*/
package edu.ilstu;

import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class part2
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		double a;
		double b;
		double c;
		double equation1;
		double equation2;
		
		Scanner scan = new Scanner(System.in);
		
		System.out.println(" Please enter the values for this equation Ax^2+Bx+c");
		
		System.out.println("Please enter a value for A^2 ");
		a = scan.nextDouble();
		System.out.println("Please enter a value for Bx ");
		b = scan.nextDouble();
		System.out.println("Please enter a value for C ");
		c = scan.nextDouble();
		
		double determinantA = b * b - 4 * a * c;
		// condition for real and different roots
		if(determinantA > 0) {
		equation1 = (-b + Math.sqrt(determinantA)) / (2 * a);
		equation2 = (-b - Math.sqrt(determinantA)) / (2 * a);
		System.out.format("The Roots  are %.2f and %.2f.\n", equation1 , equation2);
		}
		// Condition for real and equal roots
		else if(determinantA == 0) {
		equation1 = equation2 = -b / (2 * a);
		System.out.format("%.2f is a repeated solution.\n", equation1);
		}
		// If roots are not real
		else {
		System.out.format(" No real solutions or roots.\n");
		}
	
	
		// In the last part of the problem it becomes no solution because the determiant shows that there is no roots.
		//In the first we can find the regular roots and everything works
		// In the second -0.50 is a repeated solution
		

	}

}
