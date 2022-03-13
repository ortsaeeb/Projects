/*
*File name: RoomReservation.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Mar 4, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: 
*Lab Section: 3
*Lab Instructor: 
*/
package edu.ilstu;

import java.util.Date;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class RoomReservation
{
	private final double breakFast = 9.99;
	private final double crib = 14.50;
	private final double lateCheckOut = 29.99;
	private final double SALES_TAX = 0.06;
	private final double SERVICE_FEE = 0.08;
	
	private int customerName;
	private Date reservationDate;
	private double preTaxTotal;
	private double finalTotal;
	private int numVisitors;
	private int roomNumber;
	private double roomPrice;
	private boolean breakfastSelect;
	private boolean cribSelect;
	private boolean lateCheckOutSelect;
	private double extra;
	public RoomReservation()
	{
		reservationDate = new Date();
	}
	
	
	
	
	public RoomReservation(int customerName, int roomNumber, double roomPrice )
	{
		this.customerName = customerName;
		this.roomNumber = roomNumber;
		this.roomPrice = roomPrice;
	}
	
	public void setPreTaxTotal()
	{
		if(breakfastSelect)
			extra=breakFast;
		if (cribSelect)
			extra+= crib;
		if (lateCheckOutSelect)
			extra +=lateCheckOut ;
		preTaxTotal = roomPrice + extra;
		
	}
	public void setTotalPrice() 
	{
		double reservationSalesTax = preTaxTotal *SALES_TAX;
		double reservationServiceFee = preTaxTotal * SERVICE_FEE;
		finalTotal= preTaxTotal+ reservationSalesTax+reservationServiceFee;
		 
	}
	
	public String ToString()
	{
		String receipt = "\n******************************************"+
									"\n******Room " +roomNumber +"successfully reserved****"+
									"\n******************************************************"+
									"\nRoom:  $"+String.format("%.2f",roomPrice)+
									"\nExtra: $" +String.format("%.2f",extra)+
									"\nTotal before tax: $"+String.format("%.2f",preTaxTotal)+
									"\nSales Tax: $"+String.format("%.2f",preTaxTotal * SALES_TAX)+
									"\nService fee: $"+String.format("%.2f",preTaxTotal * SERVICE_FEE)+
									"\nTotal after tax: $"+String.format("%.2f",finalTotal)+
									"\n*******************************************************"+
									"\n**********Thank you for your reservation***************"+
									"\n*******************************************************";
									return receipt;
									
									
	}
	public int getNumVisitors()
	{
		return numVisitors;
	}


	public int getRoomNumber()
	{
		return roomNumber;
	}


	public boolean getBreakfastSelect()
	{
		return breakfastSelect;
	}

	public boolean getLateCheckOutSelect()
	{
		return lateCheckOutSelect;
	}

	public double getExtra()
	{
		return extra;
	}

	public int getCustomerName()
	{
		return customerName;
	}

	public double getRoomPrice()
	{
		return roomPrice;
	}

	public boolean getCribSelect()
	{
		return cribSelect;
	}
	public void setCustomerName(int customerName)
	{
		this.customerName = customerName;
	}

	public void setNumVisitors(int numVisitors)
	{
		this.numVisitors = numVisitors;
	}

	public void setroomNumber(int roomNumber)
	{
	}

	public void setRoomPrice(double roomPrice)
	{
		this.roomPrice = roomPrice;
	}

	public void setBreakfastSelect(boolean breakfastSelect)
	{
		this.breakfastSelect = breakfastSelect;
	}

	public void setCribSelect(boolean cribSelect)
	{
		this.cribSelect = cribSelect;
	}

	public void setLateCheckOutSelect(boolean lateCheckOutSelect)
	{
		this.lateCheckOutSelect = lateCheckOutSelect;
	}

	public void setExtra(double extra)
	{
		this.extra = extra;
	}
	
	
		
}
