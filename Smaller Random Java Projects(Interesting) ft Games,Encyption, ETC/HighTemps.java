package edu.ilstu;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Scanner;
/**
 *Programmer:Samson Okunola
 *
 */


public class HighTemps
{
	
		public static int [] temps;
		public HighTemps() {
			temps= new int[200];
			for(int i=0; i<temps.length;i++) {
				temps[i]=-999;
			}
		}
	   public  void fillArray()
	    {
	        int curVal;
	        
	        Scanner input = null;
	        try
	        {
	            input = new Scanner(new File("temps.txt"));
	            // set the current number of items in the array to zero
	            while (input.hasNextInt())
	            {
	                curVal = input.nextInt();
	                curVal+=40;
	                if(temps[curVal]==-999) {
	                	temps[curVal]=1;
	                }
	                else if(temps[curVal]==1) {
	                	temps[curVal]=2;
	                }
	                else if(temps[curVal]==2) {
	                	temps[curVal]=3;
	                }
	                else if(temps[curVal]==3) {
	                	temps[curVal]=4;
	                }
	                
	                // add code to store curVal into the array and update other information as needed
	            }
	            input.close();
	        }
	        catch (FileNotFoundException e)
	        {
	            System.out.println("Could not find temps.txt file");
	            System.exit(1);
	        }
	    }
	    
	public static void main(String[] args)
	{
		HighTemps high= new HighTemps();
		high.fillArray();
		System.out.println("Temp\t\t"+"Count");
			int temp=0;
		for(int i=0; i<temps.length;i++) {
			temp= i-40;
			if(temps[i]!=-999) {
				System.out.println(temp+"\t\t\t"+temps[i]);
			}
		}
		// TODO Auto-generated method stub

	}

}
