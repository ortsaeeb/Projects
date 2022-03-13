package Exp1;

public class CarApp2 {

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
		
		
		car.setPrice(15798);
		car.setMileage(62000);
		
		System.out.printf("\nThe car price is $%.2f", car.getPrice());
		System.out.printf("\nThe car milage is %.2f", car.getMileage());	
		
		System.out.printf("\n\n");
		car.setPrice(-15798);
		car.setMileage(-62000);

	}

}
