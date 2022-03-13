#include<iostream>
#include"Bank.h"
using namespace std;

int main()
{
  int numOfBanks;
  cout<<"Please Enter the Num of Banks: "<<endl;// prompting the using to enter the number of banks
  cin>> numOfBanks;

    Bank** arrayBank = new Bank*[numOfBanks];// declaring the array and creating a new object of the bank
    delete arrayBank;//deleting the pointer arrayBank

    for (int i = 0; i < numOfBanks; i++)
    {

        double amt = rand() % 200000 + 10;
        double rate = rand() % 10 + 1;
        double time = rand() % 15 + 1;
        Bank *temp = new Bank(); // creating the bank object pointing to temp

        temp ->deposit = amt;//pointing deposit to the amt, time, and rate.
        temp->interest = rate;//pointing interest to the amt, time, and rate.
        temp->timeInYears = time;//pointing timeInYears to the amt, time, and rate.
        arrayBank[i] = temp;
    }

    for (int i = 0; i < numOfBanks; i++)
    {
      cout<<"This is the simple interest rate: "<< endl;
      cout << arrayBank[i]->simpleInterest() << endl;
    }

    return 0;
}
