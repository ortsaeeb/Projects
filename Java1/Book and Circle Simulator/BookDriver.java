/*
 *File name: BookDriver.java
 *
 *Programmer:Samson Okunola
 *
 *Date:Sep 17, 2019
 *
 *Class: IT 168
 *Lecture Section: 01
 *Lecture Instructor: Qi Zhang
 *Lab Section: 03
 *Lab Instructor: Toba Adegbite
 */
package edu.iltstu;

/**
 *<insert class description here>
 *
 * @author Samson
 *
 */
public class BookDriver
{
   
	private String title;
	private double price;
	private int numsold;
	public final double SALES_TAX = .075;
	
	
	public BookDriver(String title, double price, int numsold) {
		this.title = title;
		this.price = price;
		this.numsold =numsold;
		
	}
	
	public String getTitle() {
		return this.title;
	}
	public int getnNumSold(){
		return numsold;
	}
	
	public double getPrice() {
		return this.price;
	}
	public void setTitle(String name) {
		this.title = name;
	}
	public void setPrice(double price) {
		this.price = price;
	}
	public void setNumSold(int numsold) {
		this.numsold = numsold;
	}
	
	public double getCalculateSales(double price, int numsold) {
		double calculatesales;
		calculatesales = price * SALES_TAX;
		calculatesales = price + calculatesales;
		
		calculatesales = calculatesales * numsold;
		
				
		return calculatesales;
		
		
	}

	

		
	}
	

