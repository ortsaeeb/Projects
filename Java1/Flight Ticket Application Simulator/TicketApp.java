package Exp03;
//Samson Okunola

public class TicketApp {

	public static void main(String[] args) {
		// Create an Instructor oject
		Flight myFlight = new Flight("New York", "Chicago");
		
		// Create a ticket object
		Ticket myTicket = new Ticket("N123", 620, myFlight);
		 
		// Display the tickedt information
		System.out.println(myTicket);
	}
}




