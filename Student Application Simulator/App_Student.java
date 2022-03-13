package a01_q2;
/**
 *Programmer:Samson Okunola
 *
 */

public class App_Student {

	public static void main(String[] args) {
		System.out.println("===================================");
		System.out.println("Question 2");
		System.out.println("Samson Okunola");
		System.out.println("801184329");
		System.out.println("===================================");
//new object Employee
		Employee employee1 = new Employee ("Linda Ward",26,"Female",17.8,22.7);
		
		Employee employee2 = new Employee ("Linda Ward",26,"Female",19.3,17.8);

		System.out.println(employee1.toString());
		System.out.println("----------------------");
		System.out.println(employee2.toString());
		//comparing both Employyee
		boolean compare1 =employee1.equals(employee2);
		//toString

		if(compare1)
		{
			System.out.println("\nThey are the same Person");
		}
			else
		{
			System.out.println("\nThey are not the same Person");
		}
		
		System.out.println("===================================");
		System.out.println("===================================");
	//new Object Student
	Student student1 = new Student ("James Smith",21,"Male","Computer Science",350,4);
	
	Student student2 = new Student ("James Smith",21,"Male","Information Technology",281,3);
	//toString
	System.out.println(student1.toString());
	System.out.println("----------------------");
	System.out.println(student2.toString());
//comparing both Students
	boolean compare2 =student1.equals(student2);
	if(compare2)
	{
		System.out.println("\nThey are the same Person");
	}
	else
	{
		System.out.println("\nThey are not the same Person");
	}
	
	System.out.println("===================================");

	
	
	
	

}}
