/*
*File name: Country.java
*
*Programmer: Samson Okunola
*ULID: 801184329
*
*Date:Apr 26, 2020
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
public class Country
{
	
	private String name;
	private static int employmentRate;
	private double jobSecurity;
	private double lifeExpectancy;
	private int personalEarnings;
	
	public Country(String name, int employmentRate, double jobSecurity, double lifeExpectancy, int personalEarnings)
	{
		this.name=name;
		this.employmentRate=employmentRate;
		this.jobSecurity=jobSecurity;
		this.personalEarnings=personalEarnings;
		this.lifeExpectancy=lifeExpectancy;
	}
	 public String getName()
		{
			return name;
		}

		public static int getEmploymentRate()
		{
			return employmentRate;
		}

		public double getJobSecurity()
		{
			return jobSecurity;
		}

		public double getLifeExpectancy()
		{
			return lifeExpectancy;
		}

		public int getPersonalEarnings()
		{
			return personalEarnings;
		}
		@Override
		public String toString()
		{
			if(name.length()>8&&name.length()<10) {
			name+="     ";	
			}
			if(name.length()>10&&name.length()<12) {
				name+=" ";	
				}
			if(name.length()<8) {
				name+="       ";	
				}
			return  name + "\t\t\t\t"
					+ employmentRate + "\t\t\t\t" + jobSecurity
					+ "\t\t\t\t" + lifeExpectancy
					+ "\t\t\t\t" + personalEarnings;
		}

	
	

}
