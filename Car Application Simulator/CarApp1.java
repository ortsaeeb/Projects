/**
 * 
 */
package Exp1;

public class CarApp1 {
	public static void main(String[] args) {
		Car car = new Car(2015, "Toyota", "Camry");
		
		// Clients can call toString explicitly 
		// by coding the method call.

		// explicit toString call
		System.out.println( car.toString( ) );		   
		   
		// Clients can call toString implicitly by using 
		// an object reference where a String is expected.

		// implicit toString call
		System.out.println( car );
	}
}
