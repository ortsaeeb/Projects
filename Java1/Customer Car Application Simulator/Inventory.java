/*
*File name: Inventory.java
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

import java.util.Arrays;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Inventory
{
	private final static int ARRAY_SIZE = 100;
	private Automobile[] inventory;
	private int size;
	public Automobile[] getInventory()
	{
		return inventory;
	}

	public void setInventory(Automobile[] inventory)
	{
		this.inventory = inventory;
	}

	public int getSize()
	{
		return size;
	}

	public void setSize(int size)
	{
		this.size = size;
	}

	public static int getArraySize()
	{
		return ARRAY_SIZE;
	}	
	
	/**
	 * Constructor - creates the inventory array
	 */
	public Inventory()
	{
		inventory = new Automobile[ARRAY_SIZE];
	}
	
	public void EntireInventory()
	{
	
		for(int i=0; i<ARRAY_SIZE;i++) {
			System.out.println(inventory[i].toString());
		}
		
	}
	public void displayAvailableInventory() {
		System.out.println("Displaying available inventory");
		for(int i=0; i<size;i++) {
			if(inventory[i].getStatus().equals("available")) {
				System.out.println(inventory[i].toString());
			}
			//change or verify the equals statement to check the status
	}
	}
	public void displaySoldInventory()
	{
		for(int i=0; i<size;i++) {
			System.out.println(inventory[i].toString());
			
}
	}
	public void displayBuyersMailList()
	{
		for(int i=0; i<size;i++) {
			System.out.println(inventory[i].getCustomer().toString());
			
		
	}
	}
	
	public void findExactVehicle(String vin)
	{
		System.out.println("Searching for vehicle with VIN: "+vin);
		for(int i=0; i<size;i++) {
			if(inventory[i].getVin().equals(vin)) {
				System.out.println(vin+ " was found");
				System.out.println(inventory[i].toString());
			}
			
		
		}}
	public void sortbyYear() {
		Object[] new_arr = Arrays.stream(inventory).filter(v -> v != null).sorted((v1,v2)->{
	           return ((Integer)v2.getYear()).compareTo(((Integer)v1.getYear()));
	                      
	       }).toArray();
	      
		inventory = new Automobile[new_arr.length];
	       //
	       for(int i=0;i<new_arr.length;i++)
	       {
	    	   inventory[i] = (Automobile)(new_arr[i]);
	       }
	
	
	}
}



