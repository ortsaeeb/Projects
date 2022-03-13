package a01_q2;
/**
 *Programmer:Samson Okunola
 *
 */
import java.text.DecimalFormat;

import javax.print.attribute.standard.MediaSize.Other;

public class Employee extends Person {
	private double hour;
	private double payment;
	private double rate;
	
	
	public Employee(String name,int age, String gender, double hour, double rate)
	{
		super(name,age,gender);
		
		this.rate=rate;
		this.hour=hour;
		
		name=super.getName();
		gender=super.getGender();
		age=super.getAge();
	}
	
	public double getHour() {
		return hour;
	}


	public double getPayment() {
		double newPayment=rate*hour;
		return newPayment;
	}


	public double getRate() {
		return rate;
	}

	@Override
	public String toString() {
		String objEmployee = ("The Employee's name: "+super.getName()+
				"\nAge: "+ super.getAge()+
				"\nGender: "+super.getGender()+
				"\nPayment: "+ getPayment());
		return objEmployee;
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
			Employee other = (Employee) obj;
		
		return getName().equals(other.getName()) 
				&& df.format(getPayment()).equals(df.format(other.getPayment()));
				
		}
		return false;
				
	}

}
