/*
*File name: Customer.java
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
public class Customer
{
	private String firstName;
	private String lastName;
	private String streetAddress;
	private String city;
	private String state;
	private String zip;
	private String email;
	private String phone;
	
	public Customer(String firstName, String lastName,String streetAddress, String city, String state, String zip, String email, String phone) {
		
		this.firstName= firstName;
		this.lastName= lastName;
		this.streetAddress= streetAddress;
		this.city= city;
		this.state= state;
		this.zip= zip;
		this.email= email;
		this.phone= phone;
		
	}
	
	public String getFirstName()
	{
		return firstName;
	}
	
	public String getLastName()
	{
		return lastName;
	}
	public String getStreetAddress()
	{
		return streetAddress;
	}
	
	public String getCity()
	{
		return city;
	}
	
	public String getState()
	{
		return state;
	}
	
	public String getZip()
	{
		return zip;
	}
	
	public String getEmail()
	{
		return email;
	}
	
	public String getPhone()
	{
		return phone;
	}

	@Override
	public String toString()
	{
		return    "Name:"+ firstName + lastName
				+ "streetAddress:" + streetAddress 
				+ "City/State/Zip:" + city + state + zip
				+ "Email:" + email
				+ "Phone:" + phone  ;
	}
	

}
