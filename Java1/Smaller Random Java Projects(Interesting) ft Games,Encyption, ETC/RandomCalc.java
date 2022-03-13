/*
 *File name: RandomCalc.java
 *
 *Programmer: Samson Okunola
 *
 *
 *Date:Sep 8, 2019
 *
 *Class: IT 168
 *Lecture Section: 01
 *Lecture Instructor: Qi Zhang
 *Lab Section: 03
 *Lab Instructor: Toba Adegbite
 */
package k;

import java.util.Random;

/**
 *<program to run random number generator and put 3 random numbers through 4 math equations>
 *
 * @author Samson Okunola
 *
 */
public class RandomCalc
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Random rand = new Random();
		int num1 = rand.nextInt(6)+1;
		int num2 = rand.nextInt(6)+1;
		int num3 = rand.nextInt(6)+1;
		//stating random function and random number perameters 
		
	    int math1 = num1 +num2 + num3;
		System.out.println(num1+ "+" + num2+ "+" + num3+ "=" + math1 );
		//running first math equation with random numbers
		
		int math2 = num1 - num2 - num3;
		System.out.println(num1 + "-" + num2 + "-" +  num3 + "=" + math2);	
		//running the second math equation with random numbers
		
		int math3 = num1 * num2 * num3;
		System.out.println(num1 + "*" + num2 + "*" +  num3 + "=" + math3);	
		//running third math equation with random numbers
		
		double math4 = Math.pow(num1,2);
		double math5 = Math.pow(math4, 3);
		System.out.printf(num1 + "to the power of 2 then that answer taken to the power of 3: %,.2f%n" ,  + math5);
		//running final math equation with first random number only
	}

}
