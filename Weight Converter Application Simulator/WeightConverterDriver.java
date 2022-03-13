package Exp01;
/**
 *Programmer:Samson Okunola
 *
 */
public class WeightConverterDriver {

	@SuppressWarnings("static-access")
	public static void main(String[] args) {
		// Write the statement to instantiate an 
		// object using the WeightConverter class, and name it converter.
		WeightConverter converter = new WeightConverter();
		
		// Write the call statement to the 
		// convertPoundsToKG method and store the result in 
		// variable named convertedKG
		double convertedKG = converter.convertPoundsToKG(12.5);
		
		// Write the call statement to the convertKGToPounds 
		// method and store the result in variable named convertedPounds
		double convertedPounds = converter.convertKGToPounds(3.8);
		
		// Print the value stored in the POUND_TO_KG constant
		System.out.println(converter.POUND_TO_KG);
		
		System.out.printf("\nconvertedKG = %.2f", convertedKG);
		System.out.printf("\nconvertedPounds = %.2f", convertedPounds);	
	}
}


