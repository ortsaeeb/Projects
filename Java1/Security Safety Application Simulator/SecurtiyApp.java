/*
*File name: SecurtiyApp.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Oct 28, 2019
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
public class SecurtiyApp
{
	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		Scanner scan = new Scanner(System.in);
		
		String main;
		String mainMenu;
		System.out.println("Please select a tool form the options below:");
		System.out.println("1."+ " "+ "Password Generator");
		System.out.println("2."+ " "+ "Encryption Tool");
		System.out.println("3."+ " "+ "Decription Tool");
		System.out.println("Your Selecttion: (1,2,3)>");
		while(true) {
			String tool = scan.next();
			switch (tool) {
			case "1":
				passwordSelected();
				break;
			case "2":
				encryptionSelected();
				break;
			case "3":	
				encryptionSelected();
				break;
				
			}
		String passwordSelected;
		
		System.out.println(" Enter a phrase that is at least 8 characters long");
		String keyboard2 = scan.nextLine();
		scan.hasNextLine();
		while ( keyboard2.length() < 8) {
			System.out.println("Invalid");
			System.out.println(" Enter a phrase that is at least 8 characters long");
			keyboard2 = scan.nextLine();
		}
		System.out.println(" The password is"+ " " + keyboard2);
		
	    String password =  Securtiy.generatePassword(keyboard2);
		System.out.println("The new password is" + " " + password);
		
		String encryptionSelected;
		System.out.println("Pleae select encryption type:");
		System.out.println("1." + " "+ "Ceaser Encrytion");
		System.out.println("2." + " "+ "Vigener Encrytion");
		String enc = scan.next();
		
		switch (enc) {
		
		case "1":
			System.out.println("Please Enter phrase that you want to encrypt either Caesar or Vigener");
			System.out.println("Phrase to be encrypted");
			String text = scan.next();
			System.out.println("If the encrytion needs a key, please enter it");
			String key = scan.next();
			try {
				int k = Integer.parseInt(key);
				String encryptedText = Securtiy.ceasarEncrypt(text, k);
				System.out.print("Ceasar Encrytped Text:" + encryptedText);
				
			}catch (Exception e) {
				System.out.print("Error:Wrong Key");
			}
			break;
		case "2":
			System.out.print("Vigener Encrytion");
			System.out.println("Phrase to be encrytped");
			String text2 = scan.next();
			System.out.println("Enter the new Key");
			String key2 = scan.next();
			if (key2.length() > text2.length()) {
				System.out.print("Error:  Invaild Length");	
			}
			else { 
				String encryptedText = Securtiy.vigenerEncrypt(text2 ,key2 );
			System.out.print("Vigener Encrytped Text:" + encryptedText);
			
		
		}
		
		String decryptionSelected;
		
		 System.out.print("Please Select the type of Decryption form the options below\n");
		 System.out.println("1." + " " + "Ceaser Decryption");
		 System.out.println("2." + " " + "Vigener Decryption");
	
		String dec = scan.next();
		
		switch (dec) {
		case "1":
			System.out.println("Ceaser Decryption");
			System.out.println("Text to be decrypted>");
			String text1 = scan.next();
			System.out.println("Enter Key you want to use for decryotion>");
			String key1 = scan.next();
			
			try {
				int k = Integer.parseInt(key1);
				String encryptedTExt = Securtiy.ceasarEncrypt(text1, k);
				System.out.println("Ceaser Dcrytped Text:" + encryptedTExt);
				
			}catch (Exception e) {
				System.out.println("Error Wrong Key");
			}
			break;
			
		case "2":
			System.out.println("Vigener Decryption");
			System.out.println("Text to be decrypted");
			String text21 = scan.next();
			System.out.println("Enter Key (size shold be less the n message)");
			String key21 = scan.next();
		
			if (key21.length() > text21.length()) {
			System.out.print("Error");
			}
			else {
				String encryptedText = Securtiy.vigenerEncrypt(text21, key21);
				System.out.println("Vigener Decrypted text:" + encryptedText );
				}
		
				
						break;
		default:
		
			System.out.println("Invalid Decryption Method" + dec + " Notable to be found."	);
			break;
		

	}

}
		}
	}

	private static void encryptionSelected()
	{
		// TODO Auto-generated method stub
		
	}

	private static void passwordSelected()
	{
		// TODO Auto-generated method stub
		
	}

	
	}


	