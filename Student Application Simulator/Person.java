package a01_q2;
/**
 *Programmer:Samson Okunola
 *
 */
public abstract class Person 
{
	private String name;
	private int age;
	private String gender;
	
	
	public Person(String name, int age, String gender)
	{
		this.name=name;
		this.age=age;
		this.gender=gender;
	}
	public String getName() {
		return name;
	}


	public int getAge() {
		return age;
	}


	public String getGender() {
		return gender;
	}
	
public abstract String toString();
	
public abstract boolean equal(Object obj);

}
