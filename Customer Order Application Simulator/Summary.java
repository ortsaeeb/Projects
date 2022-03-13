/*
*File name: Summary.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Mar 29, 2020
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
public class Summary
{
	private final static double TAX_RATE = 0.07;
	private final static double DELIVER_CHARGE= 3.00;
	private final static double MIN_ORDER = 20.0;
	
	
	public static double calculateSubbTotal(Order newOrder)
	{
		double subbTotal=0;
		if(newOrder.getbCount()!=0)
		{subbTotal+=newOrder.getbCount()*newOrder.getBurger();
	}
		if(newOrder.getfCount()!=0)
		{subbTotal+=newOrder.getfCount()*newOrder.getFries();
		
		}
		if(newOrder.getnCount()!=0)
		{subbTotal+=newOrder.getnCount()*newOrder.getNachos();
}
		if(newOrder.getCsCount()!=0)
		{subbTotal+=newOrder.getCsCount()*newOrder.getChickenSandwitch();
		}
		if(newOrder.gettCount()!=0)
		{subbTotal+=newOrder.gettCount()*newOrder.getTaco();
		}
		if(newOrder.getSdCount()!=0)
		{subbTotal+=newOrder.getSdCount()*newOrder.getSmallDrink();
		}
		if(newOrder.getMdCount()!=0)
		{subbTotal+=newOrder.getMdCount()*newOrder.getMediumDrink();
		}
		if(newOrder.getLdCount()!=0)
		{subbTotal+=newOrder.getLdCount()*newOrder.getLargeDrink();
		}
		
		return subbTotal;
	}
	public static double calculateNewTax(Order newOrder)
	{
		return calculateSubbTotal(newOrder)*TAX_RATE;
	}
	public static double calculateDeliveryCharge(Order newOrder)
	{
		if(newOrder.isDelivery()&&calculateSubbTotal(newOrder)<MIN_ORDER)
		{
			return DELIVER_CHARGE;
		}
		return 0;
	}
	public static double calculateTotal(Order newOrder)
	{
		return calculateSubbTotal(newOrder) + calculateNewTax(newOrder) +calculateDeliveryCharge(newOrder);
	}
	public static String outputNewSummary(Order newOrder)
	{
		String stri = "Total for the new order is: \n";
		stri+= "Subtotal: $"+String.format("%.2f", calculateSubbTotal(newOrder))+"\n";
		stri+="Tax        $"+String.format("%.2f", calculateNewTax(newOrder))+"\n";
		if(calculateDeliveryCharge(newOrder)>0)
		{
			stri+="DeliveryCharge:$"+String.format("%.2f",calculateDeliveryCharge(newOrder)+"\n");
		}
		stri+="Total:     $"+String.format("%.2f", calculateTotal(newOrder));
		return stri;
		
				
	}
	
	
}

	
		
