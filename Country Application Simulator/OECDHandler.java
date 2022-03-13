/*
*File name: OECDHandler.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Apr 26, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Arrays;
import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class OECDHandler
{
	private static Country[] data;
	private static int actualSize;
	private static final int SIZE = 50;
	
	
	public OECDHandler(Country[]data)
	{
		this.data= new Country[SIZE];
	}
		public void read(String filename) {
			try	{
			Scanner fileReader = new Scanner(new File("oecd_bli.csv"));
			fileReader.nextLine();
			while(fileReader.hasNext())
			{
				
				String line=fileReader.nextLine();
				String[] tokens= line.split(",");
				Country country= new Country(tokens[0],Integer.parseInt(tokens[1]),Double.parseDouble(tokens[2]),Double.parseDouble(tokens[3]),Integer.parseInt(tokens[4]));
				data[actualSize]= country;
				actualSize++;
			}
			}
	    catch(FileNotFoundException e)
	{
	    	e.printStackTrace();
	}
		}
		
	public void displayAllCountries()
	{
	
		for(int i=0; i<actualSize;i++) {
			System.out.println(data[i].toString());
		}
		
	}
	public void searchName (String name)
	{
		for (int i =0;i<actualSize;i++)
		{
			if (data[i].getName().contains(name))
			{
				System.out.println(data[i].toString());
				return;
			}
		}
		
		}
	public void searchByEmploymentRatee (int employmentRate)
	{
			boolean newRate =true;
		for (int i =0;i<actualSize;i++)
		{
			if (data[i].getEmploymentRate()>employmentRate)
			{
				if(newRate)
						System.out.print("Country\t\t\t"+"Employment Rate\t\t\t"+"Job Security\t\t\t"+"Life Expectancy"+"Personal Earnings");
				newRate=false;
				System.out.print(data[i]);	
				
			}
			if(!newRate)
				System.out.println("No country has an employment rate higher than"+employmentRate);
			else if(employmentRate>=100)
			{
				System.out.println("No country has an employment rate higher than 100");

			}}}
		
			private void sortCountriesByEarnings()
			{
			       Object[] new_arr = Arrays.stream(data).filter(v -> v != null).sorted((v1,v2)->{
			           return ((Integer)v2.getEmploymentRate()).compareTo(((Integer)v1.getEmploymentRate()));
			                      
			       }).toArray();
			      
			       data = new Country[new_arr.length];
			       //
			       for(int i=0;i<new_arr.length;i++)
			       {
			           data[i] = (Country)(new_arr[i]);
			       }
			}
			public void rankCountriesByEarnings ()
			{
				try
				   
				(BufferedWriter txt = new BufferedWriter(new FileWriter("countries ranked by earnings.txt",true)))
				{
					txt.append("Country\t\t" + "Employment Rate\t\t" + "Job Security\t\t" + "Life Expectancy\t\t" + "Personal Earnings");
					txt.append("\n");
				           for(int b=0;b<actualSize;b++)
				           {
				        	   txt.append(data[b].toString());
				        	   txt.append("\n");
				           }
				       }
				       catch (IOException e) {
				           e.printStackTrace();
			}
		
		}
		
			
			
		
	}
	
		
		
	
	
			
			
		
	


	
	
	


