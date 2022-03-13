/*
*File name: DiceGame.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Jul 7, 2020
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Tonya Pierce
*Lab Section: 1
*Lab Instructor: Reki Puri
*/
package edu.ilstu;

import java.util.Random;
import java.util.Scanner;

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class DiceGame
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		System.out.println("Player 1 is rolling dice");
		 Random randomNumber = new Random ();
		 String input = null;
		 String input2 = null;
		 int score = 0;
		
	        int roll = 0;
	        Random r = new Random();
	        Scanner scan= new Scanner(System.in);
	        boolean stillAbleToRoll = true;
	        int counter=0;
	        while (stillAbleToRoll) {
	            for (int i = 0; i < 5; i++) {

	                roll = r.nextInt(5 + 1);
	                System.out.println(roll + " ");
	                if (roll == 1) {
	                    score += 100;
	                } else if (roll == 2 || roll == 3 || roll == 4 || roll == 6) {
	                    score += 10;
	                } else if (roll == 5) {
	                    score += 50;
	                }
	            }

	            System.out.println("Your score was: " + score);
	            counter++;
	            if(counter==2){
	                stillAbleToRoll=false;
	            }
	            System.out.println("Do you want to keep this total");
	            input = scan.nextLine();
	           
	         
	            if(input.equals("no"))stillAbleToRoll= false;
	            
	    }
	    int roll2;
	    int score2 = 0; 
	   
	    while (stillAbleToRoll) {
	        for (int i = 0; i < 5; i++) {

	            roll2 = r.nextInt(5 + 1);
	            System.out.println(roll + " ");
	            if (roll2 == 1) {
	                score2 += 100;
	            } else if (roll2 == 2 || roll2 == 3 || roll2 == 4 || roll2 == 6) {
	                score2 += 10;
	            } else if (roll2 == 5) {
	                score2 += 50;
	            }
	        }
	        System.out.println("Your score was: " + score2);
	        counter++;
            if(counter==2){
                stillAbleToRoll=false;
            }
            System.out.println("Do you want to keep this total");
            input2 = scan.nextLine();
           
         
            if(input.equals("no"))stillAbleToRoll= false;
	       
	}


	    if(score>score2)
	    {
	    	System.out.println("Player 1 won");
	    }
	    	
	
	    if(score2>score)
	    {
	    	System.out.println("Player 2 won");
	    }
	    
	
	    if(score==score2)
	    {
	    	System.out.println("Both player scores are the same");
	    	
	    }

		 


	}

}
