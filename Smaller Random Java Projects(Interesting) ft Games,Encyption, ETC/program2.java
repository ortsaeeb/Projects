import java.util.Random;

/*
*File name: program2.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Sep 14, 2019
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class program2

{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		    Random random = new Random( );

		    // simulate the roll of a die
		    int number1 = random.nextInt( 6 ) + 1;
		    int number2 = random.nextInt (6)  + 1;
		    int number3 = random.nextInt (6)  + 1;
		    
		    //First Math Problem with Random number
		    int answer1= number1 + number2 + number3;
		    System.out.println(number1+ "+" + number2 + "+" + number3+ "=" + answer1 );
		    //Second Math Problem with Random number
		    int answer2 = number1 - number2 -number3;
		    System.out.println(number1 + "-" + number2 + "-" + number3 + "=" + answer2 );
		    // Third Math Problem with Random number
		    int answer3= number1 * number2 * number3;
		    System.out.println(number1 + "*" + number2 + "*" + number3 + "=" + answer3);
		    
		    double answer4 = Math.pow(number1,2 );
		    double answer5 = Math.pow(answer4,3);
		    System.out.printf(number1 + "to the power of 2 then take the answer and put that to the power of 3: %,.2f%n", + answer5);
		    
		    
		    
		    
		    
		    
		    
		    		
		}
		

	}

