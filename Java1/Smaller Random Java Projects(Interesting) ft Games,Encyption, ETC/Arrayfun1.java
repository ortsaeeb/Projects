/*
*File name: Arrayfun1.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Apr 14, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: 
*Lab Section: 3
*Lab Instructor: 
*/
package edu.ilstu;

import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Arrayfun1
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		
				
		Scanner scan = new Scanner(System.in);//Declare and create a Scanner object to read from the keyboard
		int []number = new int[100];//Declare and create an array that will hold up to 100 integers

		int size;//Declare a variable to keep track of the number of integers currently in the array

		
		 size = fillArray (number,scan);//Call the fillArray method described below, passing the appropriate arguments and
		// storing the result in the appropriate variable
		 
		 int product = computeProduct(number, size);//Call the computeProduct method described below, passing the appropriate
		// arguments, and print the result to the screen with an appropriate label
		 System.out.println("Product of array: "+ product);
		int f;//Ask the user for an integer and store in a variable named factor
		System.out.println("Enter an integer: ");
		f = scan.nextInt();
		
		System.out.println("count of mutiples :"+countMultples(number,size,f));//Use the countMultiples method described below to compute the number of multiples 

		System.out.println("New Array values are: ");//Use the printArray method to print out the values in the array
		printArray(number,size);
	}
	public static int fillArray(int number[], Scanner scan)//r. It must ask the user for values to add to the array, beginning at index 0,
	//stopping when the user enters -999. 
	{
		int size = 0, val;
		while(true)
		{
			System.out.print("Enter integer(-999 to exit): ");
			val = scan.nextInt();
			if(val==-999)
			break;
			number[size] = val;
			size++;
			}
			return size;
			}
	//accept two parameters
	
	public static int computeProduct(int number[], int size){
		{
		int product = 1;
		//
		for(int i=0; i<size; i++){
		product *= number[i];
		}
		return product;}//  The method
		//will return the product of the integers in the array
		}
	
	
		public static int countMultples(int number[], int size, int factor)//The method
		{//: an integer array, an
			//integer representing the number of valid values in the array, and an integer
			//representing a factor.
			int ct = 0;

			for(int i=0; i<size; i++){

			if(number[i]%factor==0)

			ct++;
			}
			return ct;
		}
		public static void printArray(int number[], int size){

					for(int i=0; i<size; i++){
					System.out.println(number[i]);
}
}
}
		

		
		
	


