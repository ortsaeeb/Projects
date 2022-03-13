/*
*File name: Part1.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Jun 4, 2020
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
public class Part1
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);
		String encryptedM  ="";
		String decryptM = "";
		
		System.out.println("Enter something random and it will be decrypt it: ");
		encryptedM= scan.nextLine();

		for(int i=0; i<encryptedM.length(); i=i+2){
	
		if(decryptM.length()>4){
		break;
		}
		
		
		decryptM = decryptM + encryptedM.charAt(i);
		}
		System.out.println(decryptM);
		}
		

	}


