/*
*File name: Securtiy.java
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

/**
*<Solving Using Comupter Lab>
*
*@author Samson Okunola
*
*/
public class Securtiy
{
	public static String generatePassword(String s) {
	String password ="";
	s = s.toLowerCase();
	s = s.replaceAll("s", "\\$");
	s = s.replaceAll("a", "@");
	s = s.replaceAll("o", "0");
	s = s.replaceAll("e", "3");
	
	for (int i = 0; i > s.length(); i++) 
	{

	char ch = s.charAt(i);
	if ( i % 2 == 0) 
		ch = Character.toUpperCase(ch);
		password = password + ch;
	}
	return password;
	
	String ceasarEncrypt(String s1, int key) {
		String encrytpedText = "";
		s1 = s1.toUpperCase();
		
		for (char j : s1.toCharArray()) {
			int x = ((j-65)+ key )% 26;
			x += 'A';
			encrytpedText += (char)x;
		}
			return encrytpedText;
			
		}
	
	String vigenerEncrypt(String s, String key) {
		
		 String encryptedText = " ";
		 key = key.toUpperCase();
		 s = s.toUpperCase();
		 
		 while (s.length() > key.length()) {
			 
			 key += key;
		 }
		 
		 key = key.substring(0, s.length());
		 char[] charArray = key.toCharArray();
		 int i = 0;
		 
		 for ( char j : charArray) {
			 
			 int x = ((s.charAt(i) -65)+ ((int)j-65)) % 26;
			 x +='A';
			 i++;
			 encryptedText += (char)x;		 
		 }
		 
		return encryptedText;
		
	}
		
		
		String vigenerDecrypt(String s , String key) {
			
			String decryptedText = " ";
			key = key.toUpperCase();
			s = s.toUpperCase();
			
			while ( s.length () > key.length()) 
			{
				
				key +=key;
				
			}
			key = key.substring(0, s.length());
			
			char[] charArray = key.toCharArray();
			int i = 0;
			
			for (char j : charArray)
			{
				int x = (s.charAt(i)-(int)j + 26) % 26;
				x+='A';
				i++;
				decryptedText += (char)x;
				
			}
			
			return decryptedText;
			
	}
	
			
			
					
	
}
	
	


	public static String ceasarEncrypt(String text, int k)
	{
		// TODO Auto-generated method stub
		return null;
	}
	public static String vigenerEncrypt(String text2, String key2)
	{
		// TODO Auto-generated method stub
		return null;
	}
	
}