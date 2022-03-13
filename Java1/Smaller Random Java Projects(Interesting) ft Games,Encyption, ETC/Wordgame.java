/*
 *File name: Wordgame.java
 *
 *Programmer: Samson Okunola
 
 *
 *Date:Sep 4, 2019
 *
 *Class: IT 168
 *Lecture Section: 01
 *Lecture Instructor: Qi Zhang
 *Lab Section: 03
 *Lab Instructor: Toba Adegbite
 */
package edu.ilstu;

import java.util.Scanner;
/**
 *<program for writing a story using user input then extracting last word of each sentence to build a random genereated sentence>
 *
 * @author Samson Okunola
 *
 */
public class Wordgame
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner in = new Scanner(System.in);
		
		System.out.println("What is your name?");
		String name = in.nextLine();
		//to gain input for the user for his name
		
		System.out.println("What is your age?");
	    String age = in.nextLine();
	    //to gain input for the user for his age
	    
	    System.out.println("Pick a city.");
	    String city = in.nextLine();
	    //to gain input for the user for his city
		
	    System.out.println("Pick a college.");
		String college = in.nextLine();
		//to gain input for the user for his college
		
		System.out.println("Pick a profession.");
		String job = in.nextLine();
		//to gain input for the user for his profession
		
		System.out.println("Pick an animal.");
		String animal = in.nextLine();
		//to gain input for the user for his favorite animal
		
		System.out.println("What is a good pet name?");
		String pet = in.nextLine();
		//to gain input for the user for his favorite pet name
		
		String story = "There once was a person named NAME who lived in CITY.\n";
		String replacestring = story.replaceAll("NAME",name).replaceAll("CITY",city);
        //code used to put users answer into first sentence	
		
		String story2 = "Even though NAME was only AGE, NAME went to college at COLLEGE.\n";
		String replacestring2 = story2.replaceAll("AGE",age).replaceAll("NAME",name).replaceAll("COLLEGE", college);
		//code used to put users answers into second sentence		
		
		String story3= "NAME graduated and went to work as a PROFESSION.\n";
		String replacestring3 = story3.replaceAll("NAME",name).replaceAll("PROFESSION",job);
		//code to put users answers into third senctence		
		
		String story4= "Soon thereafter, NAME adopted a(n) ANIMAL named PET.\n";
		String replacestring4 = story4.replaceAll("NAME",name).replaceAll("PET", pet).replaceAll("ANIMAL", animal);
		//code to put users answers into fourth sentence	
		
		String story5 = "NAME and PET both lived happily ever after!\n";
		String replacestring5 = story5.replaceAll("NAME",name).replaceAll("PET", pet);
		//code to put users answers into fifth sentnece		
		
		System.out.println(replacestring + replacestring2 + replacestring3 + replacestring4 + replacestring5);
		//code sequence to print out stroy with users unput
		
		String word = city;
		String word2 = college;
		String word3 = job;
		String word4 = pet;
		String word5= "after!";
		//code sequence to pull out certain user inputs and words from story
		
		System.out.print(" New word is: "  + word + " " + word2 + " " +word3 + " " + word4 + " " +word5);
		//code to output random generated sentence from story
		
	}
}	
				
				
		 
		
		
		
		
		
		
		
		
		
	
		

	
