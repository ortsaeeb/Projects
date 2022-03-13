package Exp01;
/**
 *Programmer:Samson Okunola
 *
 */

public class WeightConverter
{
    //KG is kilograms
	public static final double POUND_TO_KG = 0.454;

    public double convertPoundsToKG (double pounds)
    {
	   double kg = pounds * POUND_TO_KG;
	   return kg;
    }

    public double convertKGToPounds (double kg)
    {
	   double pounds = kg / POUND_TO_KG;
	   return pounds;
    }
}

