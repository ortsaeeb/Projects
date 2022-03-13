 package Exp03;
//Samson Okunola

public class Ticket {
	private String number;
	private double price;
	private Flight flight;
	
	public Ticket(String ticketNumber) {
		this.number = ticketNumber;
	}
	
	public Ticket(String ticketNumber, double ticketPrice){
		this(ticketNumber);		
		this.price = ticketPrice;
	}
	
	public Ticket(String ticketNumber, double ticketPrice,
	              Flight flightObject) {
		this(ticketNumber, ticketPrice);
		
		this.flight = new Flight(flightObject.getDepartureCity(),
	             				 flightObject.getArrivalCity());
	}
	
	public Flight getFlight() {
		return this.flight;
	}
	
	public void setFlight(Flight flight) {
		this.flight = new Flight(flight.getArrivalCity(),
						         flight.getDepartureCity());
	}
	
	public double getPrice() {
		return this.price;
	}
	
	public void setPrice(double newPrice) {
		this.price = newPrice;
	}
	
	public String toString() {
		String str = "Ticket Information:\n"
				   + "\nFlight number: " + this.number
				   + "\nFlight price: " + this.price
				   + "\n"
				   + "\nDepart and arrive cities: " + this.flight;

		return str;
	}
}




