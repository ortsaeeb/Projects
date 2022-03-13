/*
*File name: Customer.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Mar 27, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package edu.ilstu;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Customer
{
	private String fullName;
	private String address;
	private String phoneNumber;
	
	public Customer(String fN, String add, String pN)
	{
		this.fullName = fN;
		this.address = add;
		this.phoneNumber = pN;
	}
	
	public String getFullName() 
	{
		return fullName;
	
	}
	public String getAddress()
	{
		return address;
	}
	
	public void setFullName()
	{
		this.fullName = fullName;
	}
	@Override
	public String toString()
	{
		if(address.compareTo(" ")==0)
		{
			return "Name: "+fullName+"\n"+
				  "Phone: "+phoneNumber;
		}
		else
		{
			return "Name:" +fullName+"\n"+
					"Address: " + address+"\n"+
					"Phone: "+ phoneNumber;
			
					
		}
	}
	
	}

