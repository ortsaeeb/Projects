/*
*File name: RoomClass.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Mar 6, 2020
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
public class RoomClass
{

	private int roomNumber;
	private int roomCapacity;
	private int numOfBed;
	private int numOfBathroom;
	private double price;


public RoomClass(int roomNumber, int roomCapacity, int numOfBed , int numOfBathroom, double price)
{
	this.roomNumber= roomNumber;
	this.roomCapacity = roomCapacity;
	this.numOfBed = numOfBed;
	this.numOfBathroom = numOfBathroom;
	this.price = price;
	
}
public int getRoomNumber()
{
	return roomNumber;
}


public int getRoomCapacity()
{
	return roomCapacity;
}


public int getNumOfBed()
{
	return numOfBed;
}


public int getNumOfBathroom()
{
	return numOfBathroom;
}


public double getPrice()
{
	return price;
}
public void setRoomCapacity(int roomCapacity)
{
	this.roomCapacity = roomCapacity;
}
public void setPrice(double price)
{
	this.price = price;
}

@Override
public String toString() {
	return (roomNumber + ","+ numOfBed+ ","+ price);
}
public int getroomNumber()
{
	// TODO Auto-generated method stub
	return 0;
}







}
