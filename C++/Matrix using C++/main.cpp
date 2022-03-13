#include <iostream>
#include "Matrix.h"
using namespace std;

int main()
{

srand((20));

Matrix firstMatrix;// first matrix
cout<<"First Matrix: "<<endl;
firstMatrix.toString();//displaying the first matrix
cout<< endl;

Matrix secondMatrix;// second matrix
cout<<"Second Matrix: "<<endl;
secondMatrix.toString();// dispaying the second matrix
cout<< endl;

Matrix m3=firstMatrix * secondMatrix;
cout<<"Mul Matrix: "<<endl;

m3.toString();
cout<<" Assignment 1 Samson Okunola";
}

