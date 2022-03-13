/*
*File name: InputOutput.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Jul 29, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Tonya Pierce
*Lab Section: 1
*Lab Instructor: Reki Puri
*/
package edu.ilstu;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class InputOutput
{
	private Scanner keyboard = new Scanner(System.in);

	/**
	 * Reads the lines from the inventory.csv file
	 * parses them and creates objects
	 * 
	 * @param automobiles
	 * @return size
	 */
	public int readInventory(Automobile[] automobiles)
	{
		final String inventoryFile = "inventory.csv";
		int size = 0;

		Scanner input = null;
		try
		{
			input = new Scanner(new File(inventoryFile));
		}
		catch (FileNotFoundException e)
		{
			System.out.println("Unable to open file " + inventoryFile + ".");
		}

		// read header line and discard first line
		String line = input.nextLine();
		
		// create vars
		int year = 0;
		String make = "";
		String model = "";
		double price = 0.0;
		String condition = "";
		int rating = 0;
		String status = "";
		String vin = "";
		
		// Customer vars
		String firstName = "";
		String lastName = "";
		String streetAddress = "";
		String city = "";
		String state = "";
		String zip = "";
		String email = "";
		String phone = "";

		while (input.hasNext() && size < automobiles.length)
		{
			line = input.nextLine();
			String[] record = line.split(",");

			year = Integer.parseInt(record[0]);
			make = record[1];
			model = record[2];

			// If use this version, comment out the following if statements

//			if (!(record[3].equals("")))
//			{
//				price = Double.parseDouble(record[3]);
//			}
//			else
//			{
//				price = 0;
//			}
//
//			condition = record[4];
//
//			if (!(record[5].equals("")))
//			{
//				rating = Integer.parseInt(record[5]);
//			}
//			else
//			{
//				rating = 0;
//			}

			status = record[6];
			vin = record[7];
			
			// this is where the records differ
			// they either don't have buyer information or some do
			
			if (record.length > 8) 
			{
				if (!(record[8].equals("")))
					firstName = record[8];
				else
					firstName = "";
				
				if (!(record[9].equals("")))
					lastName = record[9];
				else
					lastName = "";
				
				if (!(record[10].equals("")))
					streetAddress = record[10];
				else
					streetAddress = "";
				
				if (!(record[11].equals("")))
					city = record[11];
				else
					city = "";
				
				if (!(record[12].equals("")))
					state = record[12];
				else
					state = "";
				
				if (!(record[13].equals("")))	
					zip = record[13];
				else
					zip = "";
				
				if (!(record[14].equals("")))
					email = record[14];
				else
					email = "";
				
				if (!(record[15].equals("")))
					phone = record[15];
				else
					phone = "";
				
			}
			
			// changes to integrate Customer class go below
			
//			Customer tempAutomobile = new Customer( firstName, lastName, streetAddress, city, 
//					state, zip, email, phone )
			Customer customer= new Customer(firstName,lastName,streetAddress,city,state,zip,email,phone);
			Automobile tempAutomobile= new Automobile(year, make, model, price, condition, rating, status, vin,customer);
			automobiles[size] = tempAutomobile;
			size++;
			
		} // end of while loop

		input.close();

		return size;
	}

	
}


