#include "Bank.h"
#include <iostream>
using namespace std;

double Bank::simpleInterest()
{
  return(deposit*interest*timeInYears)/100;
}
