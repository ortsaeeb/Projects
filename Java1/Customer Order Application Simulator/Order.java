/*
*File name: Order.java
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
public class Order
{
	public static final double BURGER = 5.0;
	public static final double FRIES = 2.50;
	public static final double TACO = 2.0;
	public static final double NACHOS = 6.50;
	public static final double CHICKEN_SANDWITCH = 5.25;
	public static final double SMALL_DRINK = 1.25;
	public static final double MEDIUM_DRINK = 1.75;
	public static final double LARGE_DRINK = 2.25;
	private int bCount;
	private int fCount;
	private int tCount;
	private int nCount;
	private int csCount;
	private int sdCount;
	private int mdCount;
	private int ldCount;
	private boolean isDelivery;
	
	
	public static double totalOrders;
	public static int countOrders;
	
	public Order(int burger2, int fries2, int taco2, int nacho, int chicken, boolean isDeliver)
	{
		++countOrders;
	}
	
	
	
	public Order (int smallD, int mediumD, int largeD, boolean isDeliver)
	{
		// TODO Auto-generated constructor stub
	}



	public void Order1(int smallD, int mediumD, int largeD, boolean isDeliver)
	{
		// TODO Auto-generated constructor stub
	}



	//getters
	public int getbCount()
	{
		return bCount;
	}
	public void setbCount(int bCount)
	{
		this.bCount = bCount;
	}
	public int getfCount()
	{
		return fCount;
	}
	public void setfCount(int fCount)
	{
		this.fCount = fCount;
	}
	public int gettCount()
	{
		return tCount;
	}
	public void settCount(int tCount)
	{
		this.tCount = tCount;
	}
	public int getnCount()
	{
		return nCount;
	}
	public void setnCount(int nCount)
	{
		this.nCount = nCount;
	}
	public int getCsCount()
	{
		return csCount;
	}
	public void setCsCount(int csCount)
	{
		this.csCount = csCount;
	}
	public int getSdCount()
	{
		return sdCount;
	}
	public void setSdCount(int sdCount)
	{
		this.sdCount = sdCount;
	}
	public int getMdCount()
	{
		return mdCount;
	}
	public void setMdCount(int mdCount)
	{
		this.mdCount = mdCount;
	}
	public int getLdCount()
	{
		return ldCount;
	}
	public void setLdCount(int ldCount)
	{
		this.ldCount = ldCount;
	}
	public boolean isDelivery()
	{
		return isDelivery;
	}
	public void setDelivery(boolean isDelivery)
	{
		this.isDelivery = isDelivery;
	}
	public static double getTotalOrders()
	{
		return totalOrders;
	}
	public static void setTotalOrders(double totalOrders)
	{
		Order.totalOrders = totalOrders;
	}
	public static int getCountOrders()
	{
		return countOrders;
	}
	public static void setCountOrders(int countOrders)
	{
		Order.countOrders = countOrders;
	}
	public static double getBurger()
	{
		return BURGER;
	}
	public static double getFries()
	{
		return FRIES;
	}
	public static double getTaco()
	{
		return TACO;
	}
	public static double getNachos()
	{
		return NACHOS;
	}
	public static double getChickenSandwitch()
	{
		return CHICKEN_SANDWITCH;
	}
	public static double getSmallDrink()
	{
		return SMALL_DRINK;
	}
	public static double getMediumDrink()
	{
		return MEDIUM_DRINK;
	}
	public static double getLargeDrink()
	{
		return LARGE_DRINK;
	}
	
	@Override
	public String toString()
	{
		String str = "Your Order is:\n";
		if(bCount!=0) {
			str+="Burger: "+String.format("%.2f", BURGER)+"\n";
		}
		if (fCount!=0) {
			str+="Fries:"+String.format("%.2f", FRIES)+"\n";
		}
		if (tCount!=0) {
			str+="Fries:"+String.format("%.2f", TACO)+"\n";
		}
		if (nCount!=0) {
			str+="Fries:"+String.format("%.2f", NACHOS)+"\n";
		}
		if (csCount!=0) {
			str+="Fries:"+String.format("%.2f", CHICKEN_SANDWITCH)+"\n";
		}
		if (sdCount!=0) {
			str+="Fries:"+String.format("%.2f", SMALL_DRINK)+"\n";
		}
		if (mdCount!=0) {
			str+="Fries:"+String.format("%.2f", MEDIUM_DRINK)+"\n";
		}
		if (ldCount!=0) {
			str+="Fries:"+String.format("%.2f", LARGE_DRINK)+"\n";
		}
		return str;
	}
}


	
	
		
			
	
	
	
	
	
	



