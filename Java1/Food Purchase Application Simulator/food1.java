/*
*File name: food1.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Sep 22, 2019
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package Food;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class food1
{
	private String vegetablename;
	private String fruitname;
	private double vegetableprice;
	private double fruitprice;
	private int vegetableorder;
	private int fruitorder;
	
	
	private final double SERVICE_RATE = .035;
	private final int DELIVERY_FEE = 5;
	
	
	public food1 (String vname, String fruitname , double vprice, double fruitprice, int vorder , int fruitorder)
	{
		this.vegetablename = vname;
		this.fruitname = fruitname;
		this.vegetableprice = vprice;
		this.fruitprice = fruitprice;
		this.vegetableorder = vorder;
		this.fruitorder = fruitorder;
	}	
								
		
	
	public String getVegetablename()
	{
	return vegetablename;
	}
	
	public String getFruitname()
	{
	return fruitname;
	}
	
	public final double getVegetableprice()
	{
	return vegetableprice;	
	}
	
	public final double getFruitprice()
	{
		return fruitprice;
	}
	
	public int getVetableorder()
	{
	return vegetableorder;
	}
	
	public int getFruitorder()
	{
	return fruitorder;
	}
	
	public void setVetablebname( String vegetablename)
	{
	this.vegetablename = vegetablename;
	}
	
	public void setFruitname(String fruitname)
	{
	this.fruitname = fruitname;
	}
	
	public void setVegetableprice (double vegetableprice)
	{
	this.vegetableprice = vegetableprice;
	}
	
	public void setFruitprice (double fruitprice)
	{
	this.fruitprice = fruitprice;
	}
	
	public void setVegetableorder (int vegetableorder)
	{
	this.vegetableorder= vegetableorder;
	}
	
	public void setFruitorder (int fruitorder)
	{
	this.fruitorder = fruitorder;
	}
	
	public double calculateSubtotal ()
	{
		double calculateSubtotal = this.vegetableprice * this.vegetableorder + this.fruitprice * this.fruitorder ;
		return calculateSubtotal;
	}
	  public double serviceFee() 
	  {
	    	 double serviceFee = calculateSubtotal() * SERVICE_RATE + DELIVERY_FEE;
	    	 return serviceFee;
	    	 
	  }
	    	 
	
	public double grandTotal() 
	{
	     double grandTotal = this.calculateSubtotal() + this.serviceFee();
	     return grandTotal;
	     
	}
	
	public void displayOrderSummary() {
	System.out.println(" \n----------------------------");
	System.out.printf("\n%-24s%s","Food Name:", "Pounds Ordered:");
	System.out.printf("\n%-24s%s", this.vegetablename, this.getVegetablename());
	System.out.printf("\n%-24s%s", this.fruitname, this.getFruitorder());
	
	
	
	
	
	
	
	

	
	
	
	
	
	
	}
