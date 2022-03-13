/**
 * 
 */
package edu.ilstu;
/**
 *Programmer:Samson Okunola
 *
 */
public class Car {
	private int year;
	private String maker;
	private String model;
	private double mileage;
	private double price;
	
	public Car(int 	year,
			String	maker,
			String	model)
	{
		this.year = year;
		this.maker = maker;
		this.model = model;
	}	
	
	// Setters
	public void setMileage(double newMileage)
	{
		if (newMileage > 0)
		{
			this.mileage = newMileage;
		}
	}
	
	public void setPrice(double newPrice)
	{
		if (newPrice > 0)
		{
			this.price = newPrice;
		}
	}
	
	// Getters
	public double getPrice()
	{
		return this.price;
	}
	
	public double getMileage()
	{
		return this.mileage;
	}
	
	// toString method
	public String toString()
	{
		return this.year + " " + this.maker + " " + this.model;
	}	
}
