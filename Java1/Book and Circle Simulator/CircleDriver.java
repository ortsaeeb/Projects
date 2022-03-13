/*
 *File name: CircleDriver.java
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
public class CircleDriver
{
 
	
	final static double PI = 3.14159;
	private static double radius;

	
	
	
	public CircleDriver(double r) {
		this.radius = r;
		
	}
	public CircleDriver() {
		radius = 0.0;
		
	}
	public void setRadius(double r) {
		this.radius = r;
	}
	public double getRadius(double r) {
		return r;
		
	}
	public static double getArea() {
		return  PI * (radius * radius);
	}
	public static double getDiameter() {
		return radius * 2;
	}
	public static double getCircumference() {
		return 2 * radius * PI;
	}

	}

