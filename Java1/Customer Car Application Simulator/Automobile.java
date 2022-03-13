/*
*File name: Automobile.java
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

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Automobile
{

	private int year = 0;
	private String make = "";
	private String model = "";
	private double price = 0.0;
	private String condition = "";
	private int rating = 0;
	private String status = "";
	private String vin = "";
	private Customer customer = null;
	
  
	private String firstName;
	private String lastName;
	private String streetAddress;
	private String city;
	private String state;
	private String zip;
	private String email;
	private String phone;
	
	public Automobile(int year, String make, String model, double price, 
			String condition, int rating, String status, String vin) 
	{
		super();
		this.year = year;
		this.make = make;
		this.model = model;
		this.price = price;
		this.condition = condition;
		this.rating = rating;
		this.status = status;
		this.vin = vin;
	}

	public Automobile(int year, String make, String model, double price, 
			String condition, int rating, String status, String vin, Customer customer) 
	{
		super();
		this.year = year;
		this.make = make;
		this.model = model;
		this.price = price;
		this.condition = condition;
		this.rating = rating;
		this.status = status;
		this.vin = vin;
		this.customer = customer;
	}

	public int getYear() {
		return year;
	}
	public String getVin() {
		return vin;
	}
	public String getMake() {
		return make;
	}

	public String getModel() {
		return model;
	}

	public String getStatus() {
		return status;
	}

	public Customer getCustomer() {
		return customer;
	}

	@Override
	public String toString() {
	    return String.format("%-5s %-12s %-12s %10.2f %-10s %6d %-11s %8s \n", 
	    		year, make, model, price, condition, rating, status, vin );
	}	
	
	public boolean equals(Automobile other)
	{
		boolean areEqual = false;
		if( this.vin.equals( other.vin ))
			areEqual = true;
		return areEqual;
	}
	
}


