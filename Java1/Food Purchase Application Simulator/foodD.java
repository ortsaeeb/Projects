/*
*File name: foodD.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Sep 23, 2019
*
*Class:IT 168
*Lecture Section: 1
*Lecture Instructor: Dr. Qi Zhang
*Lab Section: 3
*Lab Instructor: Oluwatoba Paul Adegbite
*/
package Food;
import java.util.Scanner;
/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class foodD
{

	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		//NEW TABLE #1
		Scanner scan = new Scanner(System.in);
		System.out.printf("\n%-24s%s", "Vegetable's Name","Price Per Pound");
		System.out.printf("\n%-24s%s", "Broccoli", "$3.12");
		System.out.printf("\n%-24s%s", "Yellow Onion", "$1.15");
		System.out.printf("\n%-24s%s", "Chili Peper", "$4.58");
		System.out.printf("\n%-24s%s", "Greens Bundle", "$2.82");
		System.out.print("\n---");
		
		
		//NEW TABLE #2
		System.out.printf("\n%-24s%s", "FRUIT'S NAME", "Price Per Pound");
	     System.out.printf("\n%-24s%s", "Apple", "$1.75");
		 System.out.printf("\n%-24s%s", "Grape", "$2.15");
		 System.out.printf("\n%-24s%s", "Lime", "$2..58");
		 System.out.printf("\n%-24s%s", "Orange", "$2.82");
		 System.out.print("\n---space");
		
		
		//SELECTION
		System.out.print ("\nPlease Select a Vegetable from the chart above");
		String picknumber1 = scan.nextLine();
		System.out.print ( "\nPlease enter the price per pound from the chart above");
		double pricenum1 = scan.nextDouble ();
		
		
		//SELECTION
		System.out.print ("\nPLEASE SELECT A FRUIT FROM ABOVE");
		String picknumber2 = scan.nextLine ();
		System.out.print ("\nPLEASE ENTER THE PRICE PER POUND OF THE FRUIT YOU PICKED ");
		double pricenumber2 = scan.nextDouble ();
		
		
		
		//PRICES OBJ
		System.out.printf("\n%-24s%s", "Name:", "Price Per Pound:");
	     System.out.printf("\n%-24s%s", picknumber1, "$" +pricenum1 );
	     System.out.printf("\n%-24s%s", picknumber2, "$" +pricenumber2);
	     System.out.print("\n---");
	     
	     //POUNDS OBJ
	     System.out.print("\nEnter the pound of" + picknumber1 + " ordered:");
	     int num1 = scan.nextInt();
	     System.out.print("\nEnter the pound of" + picknumber2 + " ordered:");
	     int num2 = scan.nextInt();
	     
	     
         scan.close();
	     
		
	     
	     
	     
	     
	     
		
		
		
		
		
		
		
		
		

	}

}
