/*
*File name: MoreArrayFun.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Apr 21, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;

import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class MoreArrayFun
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		int p =0;
		Scanner scan = new Scanner(System.in);
		ArrayMatnager newFile = new ArrayMatnager();
		newFile.fillArray();
		System.out.println("-------------------------------------------------------" );
		System.out.println("----------------------These are The values---------------------------------" );
		System.out.println("-------------------------------------------------------" );
		System.out.println("Largest Value "+ newFile.maxValue());
		System.out.println("Smallest Value "+ newFile.minValue());
		
		do
		{
			System.out.println("Please enter a value");
			p = scan.nextInt();
			
			
			if (p!= -999&&newFile.locationIndex(p) != 1)
				System.out.println("The number you entered is "+ newFile.locationIndex(p));
			else if(p!=999)
			{
				System.out.println("Out of bounds");
			}
				
		}while (p != -999);
	}


		
		
		
		
		
	

	}


