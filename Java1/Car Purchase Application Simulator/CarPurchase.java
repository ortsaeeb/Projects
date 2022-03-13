/**
 * 
 */
package edu.ilstu;

import java.text.NumberFormat;
import java.util.Date;

/**
 *Programmer:Samson Okunola
 *
 */
public class CarPurchase {
	private Date purchaseDate;
	private double purchasePrice;
	private String carDescription;
	
	private double carPrice;
	private double carTax;
	private double carSubtotal;
	
	private boolean hasOilChangePackage;	
	private double packagePrice;
	private double packageTax;
	private double packageSubtotal;
	
	public static final double CAR_SALES_TAX_RATE = 0.075;
	public static final double SERVICE_TAX_RATE = 0.07;
	public static final double OIL_CHANGE_PKG = 119.99;
	
	public CarPurchase() {
		purchaseDate = new Date();
	}
	
	public CarPurchase(String carDescription, double carPrice)
	{
		this();
		this.setCarDescription(carDescription);
		this.setCarPrice(carPrice);		

	}
	
	// Setters
	public void setCarDescription(String newCarDescription)
	{
		this.carDescription = newCarDescription;
	}
	
	public void setCarPrice(double newCarPrice)
	{
		carPrice = newCarPrice;
		carTax = Math.round((carPrice * CAR_SALES_TAX_RATE) * 100) / 100.0;
		
		carSubtotal = carPrice + carTax;
		this.purchasePrice = this.carSubtotal + this.packageSubtotal;
	}	
		
	public void setOilChangePackage(boolean newOilChangePackage)
	{
		hasOilChangePackage = newOilChangePackage;
		calculatePurchaseCosts();
	}
	
	// Getters
	public String getCarDescription()
	{
		return this.carDescription;
	}
	
	public double getCarPrice()
	{
		return this.purchasePrice;
	}
	

		
	private void calculatePurchaseCosts()
	{
		this.packageTax = 0;
		
		if (this.carPrice > 0)
		{
			
			if (this.hasOilChangePackage)
			{
				this.packagePrice += CarPurchase.OIL_CHANGE_PKG;
			}
		}

		this.packageTax = Math.round((this.packagePrice * CarPurchase.SERVICE_TAX_RATE) * 100) / 100.0;
		this.packageSubtotal = this.packagePrice + this.packageTax; 

		this.purchasePrice = this.carSubtotal + this.packageSubtotal;
	}
	
	
	public String toString()
	{
		NumberFormat cur = NumberFormat.getCurrencyInstance();
		String line	= "\n--------------------------------------------------";
		String layout = "\n%-40s%10s";
		
		String msg 
			= line
			+ "\nAUTO SALES ORDER RECEIPT"
		 	+ "\nOrder Date: " + purchaseDate.toString()
		 	+ line
		 	+ String.format(layout, "Item", "Amount")
			+ line
			+ String.format(layout, "Vehicle", "")
			+ String.format(layout, "\t" + carDescription , "")
			+ String.format(layout, "  Sale Price", cur.format(carPrice))
			+ String.format(layout, "  Sales Tax", cur.format(carTax))
			+ String.format(layout, "  Subtotal", cur.format(carSubtotal))
			+ "\n"
		;
		
		msg += String.format(layout, "Service Package", "");
		
		if (this.hasOilChangePackage)
		{
			msg += String.format(layout, "\tOil change package", "");
		}

		msg = msg
			+ String.format(layout, "  Sale Price", cur.format(this.packagePrice))
			+ String.format(layout, "  Sales Tax", cur.format(this.packageTax))
			+ String.format(layout, "  Subtotal", cur.format(this.packageSubtotal))
			+ line
			+ String.format(layout, "Total Cost", cur.format(this.purchasePrice))
			+ line
		;
				 
		return msg;
	}
}
