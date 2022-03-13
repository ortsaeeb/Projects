package SalaryClass;
/**
 *Programmer:Samson Okunola
 *
 */
public class Salary {
	private double hours;
	private double payPerHour;
	
	public Salary()
	{
		this.hours = 0;
		this.payPerHour = 0;
	}
	
	public Salary(double hours, double payPerHour)
	{
		this.hours = hours;
		this.payPerHour = payPerHour;		
	}
	
	public double getPayPerHour()
	{
		return this.payPerHour;		
	}
	
	public double getHours()
	{
		return this.hours;		
	}
	
	public void setPayPerHour (double payPerHour)
	{
		this.payPerHour = payPerHour;		
	}
	
	public void setHours(double hours)
	{
		this.hours = hours;		
	}
	
	public double calcSalary()
	{
		return this.getHours() * this.getPayPerHour();
	}
}
