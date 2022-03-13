#include<iostream>
#include"Bank.h"
using namespace std;

int main()
{
  int numOfBanks;
  cout<<"Please Enter the Num of Banks: "<<endl;// prompting the using to enter the number of banks
  cin>> numOfBanks;

    Bank** arrayBank = new Bank*[numOfBanks];
    delete arrayBank;

    for (int i = 0; i < numOfBanks; i++)
    {

        double amt = rand() % 200000 + 10;
        double rate = rand() % 10 + 1;
        double time = rand() % 15 + 1;
        Bank *temp = new Bank(); // creating the bank object pointing to temp

        temp ->deposit = amt;//pointing to the amt, time, and rate.
        temp->interest = rate;//pointing to the amt, time, and rate.
        temp->timeInYears = time;//pointing to the amt, time, and rate.
        arrayBank[i] = temp;
    }

    for (int i = 0; i < numOfBanks; i++)
    {
      cout<<"This is the simple interest rate: "<< endl;
      cout << arrayBank[i]->simpleInterest() << endl;
    }

    return 0;
}
