/*
*File name: dw.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Aug 7, 2020
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
public class Address
{
	private int streetNumber;
	private String streetName;
	private String city;
	private String state;
	private int zip;
	
	public  Address( int streetNumber, String streetName, String city, String state, int zip )
	{
		this.streetNumber = streetNumber;
		this.streetName = streetName;
		this.city = city;
		this.state = state;
		this.zip = zip;
				
	}
	public int getStreetNumber()
	{
		return streetNumber;
	}

	public void setStreetNumber(int streetNumber)
	{
		this.streetNumber = streetNumber;
	}

	public String getStreetName()
	{
		return streetName;
	}

	public void setStreetName(String streetName)
	{
		this.streetName = streetName;
	}

	public String getCity()
	{
		return city;
	}

	public void setCity(String city)
	{
		this.city = city;
	}

	public String getState()
	{
		return state;
	}

	public void setState(String state)
	{
		this.state = state;
	}

	public int getZip()
	{
		return zip;
	}

	public void setZip(int zip)
	{
		this.zip = zip;
	}
	@Override
	public String toString()
	{
		return streetNumber + " "+ streetName+ " \n"+
				city + " ,"+state+ zip;				
	}
	
	
	
}
