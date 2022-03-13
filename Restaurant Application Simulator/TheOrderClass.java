/*
*File name: TheOrderClass.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Feb 20, 2020
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
public class TheOrderClass
{
	public int countSalmon;
	public int countChicken;
	public int countSteak;
	public int countLamb;
	public int countFries;
	public int countSalad;
	double costSalmon= 18.00;
	double costChicken= 12.25;
	double costSteak = 19.89;
	double costLamb = 15.59;
	double costFries = 2.99;
	double costSalad = 4.99;
	final double TAX_RATE = 0.07;
	final double serviceFee = 0.010;
	int calSubTotal=0;
	double finalTax;
	double serviceCharge;
	double totalCharge;
	
	public int getCountSalmon()
	{
		return countSalmon;
	}
	public void setCountSalmon(int countSalmon)
	{
		this.countSalmon = countSalmon;
	}
	public int getCountChicken()
	{
		return countChicken;
	}
	public void setCountChicken(int countChicken)
	{
		this.countChicken = countChicken;
	}
	public int getCountSteak()
	{
		return countSteak;
	}
	public void setCountSteak(int countSteak)
	{
		this.countSteak = countSteak;
	}
	public int getCountLamb()
	{
		return countLamb;
	}
	public void setCountLamb(int countLamb)
	{
		this.countLamb = countLamb;
	}
	public int getCountFries()
	{
		return countFries;
	}
	public void setCountFries(int countFries)
	{
		this.countFries = countFries;
	}
	public int getCountSalad()
	{
		return countSalad;
	}
	public void setCountSalad(int countSalad)
	{
		this.countSalad = countSalad;
	}
	public double getCostSalmon()
	{
		return costSalmon;
	}
	public void setCostSalmon(double costSalmon)
	{
		this.costSalmon = costSalmon;
	}
	public double getCostChicken()
	{
		return costChicken;
	}
	public void setCostChicken(double costChicken)
	{
		this.costChicken = costChicken;
	}
	public double getCostSteak()
	{
		return costSteak;
	}
	public void setCostSteak(double costSteak)
	{
		this.costSteak = costSteak;
	}
	public double getCostLamb()
	{
		return costLamb;
	}
	public void setCostLamb(double costLamb)
	{
		this.costLamb = costLamb;
	}
	public double getCostFries()
	{
		return costFries;
	}
	public void setCostFries(double costFries)
	{
		this.costFries = costFries;
	}
	public double getCostSalad()
	{
		return costSalad;
	}
	public void setCostSalad(double costSalad)
	{
		this.costSalad = costSalad;
	}
	public double getTAX_RATE()
	{
		return TAX_RATE;
	}
	public double getServiceFee()
	{
		return serviceFee;
	}
	public TheOrderClass(int countSalmon,int countChicken,int countSteak, int countLamb, int countFries, int countSalad)
	{
		this.countSalmon= countSalmon;
		this.countChicken =countChicken;
		this.countSteak = countSteak;
		this.countLamb = countLamb;
		this.countSalad = countSalad;
		this.countFries = countFries;
	}
	public double calculateSubTotal()
	{
		return calSubTotal  = (int) ((int) (costSalmon*countSalmon)+(costChicken*countChicken)+(costSteak*countSteak)+(costLamb*countLamb)+(costSalad *countSalad)+(costFries * countFries));
		
	}
	public double calculateTax()
	{
		finalTax = calSubTotal* TAX_RATE;
		return finalTax;
	}
	public double calculateServiceCharge()
	{
		serviceCharge = (calSubTotal*serviceFee);
		return serviceCharge;
	}
	public double calculateTotalCharge()
	{
		totalCharge = (calSubTotal + finalTax+ serviceCharge);
		return totalCharge;
	}
	
	
	{
		
	}
}