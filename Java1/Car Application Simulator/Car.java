package Exp1;

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
		else
		{
			System.out.println("The input mileage must be greater than zero");
		}
	}
	
	public void setPrice(double newPrice)
	{
		if (newPrice > 0)
		{
			this.price = newPrice;
		}
		else
		{
			System.out.println("The input car price must be greater than zero");
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