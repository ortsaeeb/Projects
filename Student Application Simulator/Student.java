package a01_q2;

/**
 *Programmer:Samson Okunola
 *
 */
import java.text.DecimalFormat;

public class Student extends Person {
	
	private String major;
	private double totalGrade;
	private int numberOfCources;
	
	public Student(String name, int age, String gender,	String major, double totalGrade, int numberOfCources)
	{
		super(name,age,gender);//calling from the person superclass
		
		this.major=major;
		this.totalGrade=totalGrade;
		this.numberOfCources=numberOfCources;
		
		
		
		gender=super.getGender();
		name=super.getGender();
		age=super.getAge();
	}
	public double getAverageGrade()
	{
		double averageNewGrade = totalGrade/numberOfCources;
		return averageNewGrade;
	}
	
	

	@Override
	public String toString() {
		DecimalFormat df = new DecimalFormat("#.##");

		String objStudent= ("The Employee's name: "+super.getName()+
				"\nAge: "+ super.getAge()+
				"\nGender: "+super.getGender()+
				"\nMajor: "+major+
				"\nAverage Grade: "+df.format(getAverageGrade()));
		return objStudent;
	}

	@Override
	public boolean equal(Object obj) {
		DecimalFormat df = new DecimalFormat("#.##");
		if(obj==this)
		{
			return true;
		}else if(obj==null)
		{
			return false;
		}else if(this.getClass()==obj.getClass())
		{
			Student other = (Student) obj;
		
		return getName().equals(other.getName()) 
				&& (major.equals(df.format(other.major)));
				
		}
		return false;
	}

}
