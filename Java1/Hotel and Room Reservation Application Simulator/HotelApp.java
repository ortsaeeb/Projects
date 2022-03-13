/*
*File name: HotelApp.java
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

import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class HotelApp
{

	/**
	 * @param args
	 */
	public static RoomClass selectRoom(RoomClass[] newRooms)
	{
		{
			Scanner scan = new Scanner(System.in);
			
			System.out.println("*******************************************");
			System.out.println("******Welcome to The Best Bed & BreakFast**");
			System.out.println("*******************************************");
			System.out.println("\nCurrently we have these rooms available: ");
			
			for(int i = 0;i<newRooms.length;i++)
			System.out.println((( newRooms[i]).getRoomNumber()+", "+
								(( newRooms[i]).getNumOfBed()+" bed,$"+
								( newRooms[i]).getPrice())));
			System.out.println("Please type in the room number you would like to reserve: ");
			int roomNum = scan.nextInt();
			System.out.println("You have selected room number: "+roomNum);
			
			for(int i =0;i<newRooms.length;i++)
				if(roomNum==newRooms[0].getRoomNumber())
				return newRooms[i];
			return null;

			
	}
	}
	public static boolean[] selectExtra()
	{
		
		boolean breakFastChecked=false;
		Scanner input = new Scanner(System.in);
		System.out.println("would you like to add breakfast? (Yes/No): ");
		if(input.next().equalsIgnoreCase("No"))
		breakFastChecked=true;
	
		boolean cribSelect =false;
		System.out.println("would you like to add a crib? (Yes/No): ");
		if(input.next().equalsIgnoreCase("No"))
			cribSelect=true;
	
	boolean lateCheckOutSelect =false;
	System.out.println(" would you like to add late checkout? (Yes/No)");
	if(input.next().equalsIgnoreCase("No"))
		lateCheckOutSelect=true;
	boolean[] extras = {lateCheckOutSelect,breakFastChecked,cribSelect};
		return extras;
		}
	
	
	public static void printReservation(RoomReservation reservation)
	{
		System.out.println(reservation);
}
		public static void main(String[]args)
		{
			RoomClass[]newRooms = new RoomClass[3];
			newRooms[0]= new RoomClass(101,3,3,2,350);
			newRooms[1]= new RoomClass(103,3,2,2,200);
			newRooms[2]= new RoomClass(204,3,1,1,150);
			
			//rooms
			RoomClass selectRoom = selectRoom(newRooms);
			boolean []extra = selectExtra();
			
			//new reservation
			RoomReservation reservation = new RoomReservation();
			reservation.setroomNumber(selectRoom.getroomNumber());
			reservation.setRoomPrice(selectRoom.getPrice());
			reservation.setBreakfastSelect(extra[0]);
			reservation.setCribSelect(extra[1]);
			reservation.setLateCheckOutSelect(extra[2]);
			reservation.setPreTaxTotal();
			reservation.setTotalPrice();
			printReservation(reservation);

			
		}
		

}
