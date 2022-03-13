#ifndef BANK_H_
#define BANK_H_
using namespace std;

class Bank
{
  public:
    double deposit;
    double interest;
    double timeInYears;

    double simpleInterest();

};
#endif
